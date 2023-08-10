from typing import Generator
from sys import argv
from pathlib import Path
from danielutils import get_directories, get_files, error, warning, info
from bs4 import BeautifulSoup as bs4
from gp_wrapper import GooglePhotos, GooglePhotosAlbum, GooglePhotosMediaItem
from tqdm import tqdm

gp = GooglePhotos(quota=30)
EXISTING_ALBUMS = {a.title: a for a in GooglePhotosAlbum.get_albums(gp)}
INDEX_FILE_NAME = "index.html"
HR_FOLDER_NAME = "images"
IMAGE_PAGES = "imagepages"


class Album:
    """a wrapper class to simply uploading the data
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self.files = get_files(path)
        self.folders = get_directories(path)
        self.name = Path(self.path).stem

    def _setup_album(self) -> GooglePhotosAlbum:
        if INDEX_FILE_NAME not in self.files:
            error(f"\t{self.name}: No {INDEX_FILE_NAME}")
            raise ValueError(
                f"Can't process album as there is no '{INDEX_FILE_NAME}' file")
        with open(f"{self.path}/{INDEX_FILE_NAME}", "r", encoding="utf8") as f:
            index_html = f.read()
        soup = bs4(index_html, features="html.parser")
        texts: Generator[str, None, None] = (
            span.text for span in soup.find_all("span"))
        filtered_texts: Generator[str, None, None] = (t.strip()
                                                      for t in texts if len(t.strip()) > 0)
        album_title = next(filtered_texts)

        if album_title not in EXISTING_ALBUMS:
            album = gp.create_album(album_title)
        else:
            return EXISTING_ALBUMS[album_title]

        try:
            description_title = next(filtered_texts)
            chunks: list[str] = []
            tmp_chunk = ""
            for text in filtered_texts:
                if len(tmp_chunk) + len(text) >= 1000:
                    chunks.append(tmp_chunk)
                    tmp_chunk = ""
                tmp_chunk += text
            # the order matters
            for chunk in chunks[::-1]:
                album.add_description(chunk)
            album.add_description(description_title)
        except StopIteration:
            warning(f"\tno album description found")

        return album

    def _upload_media(self, album: GooglePhotosAlbum) -> None:
        if HR_FOLDER_NAME not in self.folders:
            error(f"{self.name}: No {HR_FOLDER_NAME}/")
            return

        hr_images = [
            f"{self.path}/{HR_FOLDER_NAME}/{f}" for f in get_files(f"{self.path}/{HR_FOLDER_NAME}")]

        if album.mediaItemsCount >= len(hr_images):
            info(f"\tSkipping {self.name}")
            return

        for image in tqdm(hr_images):
            try:
                image_name = image.split(
                    "/")[-1].replace("hr", "").split(".")[0]
                media: GooglePhotosMediaItem = album.add_media([image])[
                    1][0]
                with open(f"{self.path}/{IMAGE_PAGES}/{image_name}.html", "r", encoding="utf8") as f:
                    media_html = f.read()
                media_soup = bs4(media_html, features="html.parser")
                try:
                    description = media_soup.find_all(
                        "div", {"class": "imagetitle"})[0].contents[0]
                    media.set_description(description)
                except Exception as e:
                    warning(f"{image} has no description")
            except Exception as e:
                error(f"{image} has failed!")

    def upload(self) -> None:
        """uploads an album along with relevant data
        """
        try:
            info(f"Processing {self.name}")
            info("\tAcquiring album")
            album: GooglePhotosAlbum = self._setup_album()
            self._upload_media(album)
        except Exception as e:
            error(f"Failed to process {self.name}")
            print(e)


def main() -> None:
    base_folder = argv[1]
    for album_folder in get_directories(base_folder)[2:]:
        Album(f"{base_folder}/{album_folder}").upload()


if __name__ == "__main__":
    main()
