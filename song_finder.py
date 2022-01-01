import requests
from youtube_dl import YoutubeDL


def find(url: str):
    """
    傳回值:\n
        None -> 不支援或錯誤\n
        0 -> 格式錯誤\n
        Tuple -> [0]為stream網址、[1]為歌曲名稱、[2]為原檢測網址
    """
    if url.startswith("https://streetvoice.com/") or url.startswith("http://streetvoice.com/"):
        s = url.split("/")
        s = list(filter(None, s))  # remove all empty string from list?
        if s[-1].isnumeric and s[-2] == "songs":
            return streetvoice(s[-1]), streetvoice_title(s[-1]), url
        else:
            return 0
    elif url.startswith("https://www.youtube.com/watch?v=") or url.startswith("http://www.youtube.com/watch?v="):
        s = yt(url)
        if not s[0]:
            return 0
        return s

def streetvoice(id: str):
    r = requests.post("https://streetvoice.com/api/v4/song/" + id + "/hls/file/", data={})
    return r.json()['file']

def streetvoice_title(id: str):
    r = requests.get("https://streetvoice.com/api/v4/song/" + id)
    return r.json()['name']

def yt(url):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(etx)s',
            'quiet': False
        }
        
        ydl = YoutubeDL(ydl_opts)
        r = ydl.extract_info(url, download=False)
        return r['formats'][0]['url'], r['title'], url
    except:
        return None

if __name__ == "__main__":
    print(find('https://www.youtube.com/watch?v=UzvVylxqOug&ab_channel=HiroyukiSawano-Topic'))
