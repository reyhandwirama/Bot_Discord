import youtube_dl


def judulvideo(url):
  YDL_OPTIONS = {'format':"bestaudio" ,"quite":True}
  with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
    info_dict = ydl.extract_info(url, download=False)
    video_title = info_dict.get('title', None)
    return video_title
