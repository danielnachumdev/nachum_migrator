from typing import Optional
from sys import argv
from danielutils import get_directories, get_files, error
from bs4 import BeautifulSoup as bs4
from gp_wrapper import GooglePhotos, GooglePhotosAlbum, GooglePhotosMediaItem
gp = GooglePhotos()
EXISTING_ALBUMS = {a.title: a for a in GooglePhotosAlbum.get_albums(gp)}


def handle_album(album_folder: str) -> None:
    files = get_files(album_folder)
    folders = get_directories(album_folder)
    INDEX = "index.html"
    if INDEX not in files:
        error(f"{album_folder}: No {INDEX}")
        return
    with open(f"{album_folder}/{INDEX}", "r", encoding="utf8") as f:
        index_html = f.read()
    soup = bs4(index_html, features="html.parser")
    titles = soup.find_all("title")
    album_title: Optional[str] = None
    if len(titles) == 1:
        album_title = titles[0].contents[0]

    if album_title not in EXISTING_ALBUMS:
        album = gp.create_album(album_title)
    else:
        album = EXISTING_ALBUMS[album_title]

    del soup, titles, album_title, index_html

    HR_FOLDER = "images"
    if HR_FOLDER not in folders:
        error(f"{album_folder}: No {HR_FOLDER}/")
        return

    hr_images = [
        f"{album_folder}/{HR_FOLDER}/{f}" for f in get_files(f"{album_folder}/{HR_FOLDER}")]
    IMAGE_PAGES = "imagepages"
    for image in hr_images:
        image_name = image.split("/")[-1].replace("hr", "").split(".")[0]
        media: GooglePhotosMediaItem = album.add_media([image])[1][0]
        with open(f"{album_folder}/{IMAGE_PAGES}/{image_name}.html", "r", encoding="utf8") as f:
            media_html = f.read()
        media_soup = bs4(media_html, features="html.parser")
        try:
            description = media_soup.find_all(
                "div", {"class": "imagetitle"})[0].contents[0]
            media.set_description(description)
        except:
            pass


def main() -> None:
    base_folder = argv[1]
    for album_folder in get_directories(base_folder):
        handle_album(f"{base_folder}/{album_folder}")
        break


if __name__ == "__main__":
    main()
