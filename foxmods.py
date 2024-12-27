import http.client
import difflib
import json
import re
import os


mod_path: str = r"D:\SteamLibrary\steamapps\common\Foxhole\War\Content\Paks"

links: list = [
    "https://danetello.itch.io/foxhole-map-mod-fix-for-update-59",
    "https://liquidpopsicle.itch.io/liquid-sound-overhaul",
    "https://fudgelfox.itch.io/foxhole-road-center-lines",
    "https://kfczingerbox.itch.io/foxhole-coloured-cursors",
    "https://wowitsafox.itch.io/foxhole-anthem-flags",
    "https://rustard.itch.io/improved-map-mod",
    "https://kocmodecaht.itch.io/foxhole-better-compass",
    "https://sentsu.itch.io/foxhole-ui-label-icons",
    "https://ceeps.itch.io/chadblue-simplered-ui",
]


def get_used(filename: str) -> str:
    temp_files: list = [file.replace("War-WindowsNoEditor_", "") for file in os.listdir(mod_path)]
    temp_filename: str = filename.replace("War-WindowsNoEditor_", "")

    matches: list = difflib.get_close_matches(temp_filename, temp_files, cutoff=.95)

    if matches:
        return f"War-WindowsNoEditor_{matches[0]}"

    return None


def download_files(mods: dict) -> None:
    base: str = "itchio-mirror.cb031a832f44726753d6267436f3b414.r2.cloudflarestorage.com"

    for filename, mod_data in mods.items():
        url, link, version = mod_data
        used: str = get_used(filename=filename)
        data: bytes = None

        if used is None:
            continue

        conn = http.client.HTTPSConnection(base)
        conn.request("GET", url, "", {})
        res = conn.getresponse()

        file_size: int = os.path.getsize(f"{mod_path}/{used}")
        size: int = int(res.getheader("Content-Length"))

        i: int = 0

        while size < 120 and i < 5:
            data: bytes = res.read()

            if b"ExpiredRequest" not in data:
                break

            conn.close()

            print("\nError, retry....", link)

            if version == 2:
                url: str = get_mods_download_links_second(link=link)[filename][0]
            else:
                url: str = get_mods_download_links(link=link)[filename][0]

            conn = http.client.HTTPSConnection(base)
            conn.request("GET", url, "", {})
            res = conn.getresponse()

            size: int = int(res.getheader("Content-Length"))

            i += 1

        print("-", f"CHECK {filename} ({file_size}) -> ({size})")

        if file_size != size or filename != used:
            print("\nUPDATING", used, "->", filename)

            if data is None:
                data: bytes = res.read()

            os.remove(f"{mod_path}/{used}")

            with open(f"{mod_path}/{filename}", "wb") as f:
                f.write(data)

        conn.close()


def make_request(conn, method: str, endpoint: str) -> str:
    conn.request(method, endpoint, "", {})
    res = conn.getresponse()
    return res.read().decode("utf-8")


def get_mods_download_links_second(link: str) -> dict:
    base: str = link.split("//")[1].split("/")[0]
    endpoint: str = link.split(base)[1]

    conn = http.client.HTTPSConnection(base)
    res = make_request(conn, method="GET", endpoint=endpoint)

    temp_url: str = json.loads(res).get("url").split(base)[1]

    content: str = make_request(conn, method="GET", endpoint=temp_url)

    mods_name: list = re.findall(r'title="([^<]+\.pak)"', content)
    up_ids: list = re.findall(r'data-upload_id="([^"]+)"', content)

    mods_link: dict = {}

    for mod, uid in zip(mods_name, up_ids):
        if not mod.startswith("War-WindowsNoEditor_"):
            mod: str = f"War-WindowsNoEditor_{mod}"

        address: str = f"{endpoint}/file/{uid}?source=view_game&as_props=1&after_download_lightbox=true"

        res: str = make_request(conn, method="POST", endpoint=address)
        url: dict = json.loads(res)

        mods_link[mod]: list = [url.get("url"), link]

    conn.close()

    return mods_link


def get_mods_download_links(link: str) -> dict:
    version: int = 1

    base: str = link.split("//")[1].split("/")[0]
    endpoint: str = link.split(base)[1]

    conn = http.client.HTTPSConnection(base)

    content: str = make_request(conn, method="GET", endpoint=endpoint)

    # content_id: str = content.split('content="games/')[1].split('"')[0]
    mods_name: list = re.findall(r'title="([^<]+\.pak)"', content)
    up_ids: list = re.findall(r'data-upload_id="([^"]+)"', content)

    if not up_ids:
        version: int = 2

        res: str = make_request(conn, method="POST", endpoint=f"{endpoint}/download_url")

        temp_url: str = json.loads(res).get("url").split(base)[1]

        content: str = make_request(conn, method="GET", endpoint=temp_url)

        mods_name: list = re.findall(r'title="([^<]+\.pak)"', content)
        up_ids: list = re.findall(r'data-upload_id="([^"]+)"', content)

    mods_link: dict = {}

    for mod, uid in zip(mods_name, up_ids):
        if not mod.startswith("War-WindowsNoEditor_"):
            mod: str = f"War-WindowsNoEditor_{mod}"

        address: str = f"{endpoint}/file/{uid}?source=view_game&as_props=1&after_download_lightbox=true"

        res: str = make_request(conn, method="POST", endpoint=address)

        url: dict = json.loads(res)

        mods_link[mod]: list = [url.get("url"), link, version]

    conn.close()

    return mods_link


for link in links:
    print(link, "\n")
    mods_link: dict = get_mods_download_links(link=link)
    download_files(mods=mods_link)
    print("")
