from typing import Generator, Callable
from sys import argv
from pathlib import Path
from danielutils import get_directories, get_files, error, warning, info, ColoredText
from bs4 import BeautifulSoup as bs4
from gp_wrapper import GooglePhotos, GooglePhotosAlbum, GooglePhotosMediaItem
from tqdm import tqdm

INDEX_FILE_NAME = "index.html"
HR_FOLDER_NAME = "images"
IMAGE_PAGES = "imagepages"
_INFO = ColoredText.yellow("INFO")+":"
_WARNING = ColoredText.orange("WARNING")+":"
_ERROR = ColoredText.red("ERROR")+":"
MARGIN = len(_WARNING)+4
INFO, WARNING, ERROR = [s.ljust(MARGIN) for s in [_INFO, _WARNING, _ERROR]]


def logic() -> None:
    print(f"{INFO}Initializing GooglePhotos")
    gp = GooglePhotos(quota=30)
    EXISTING_ALBUMS = {a.title: a for a in GooglePhotosAlbum.get_albums(gp)}

    class Album:
        """a wrapper class to simply uploading the data
        """

        def __init__(self, path: str, logging_function: Callable[[str], None]) -> None:
            self.path = path
            self.files = get_files(path)
            self.folders = get_directories(path)
            self.name = Path(self.path).stem
            self.log = logging_function

        def _setup_album(self) -> GooglePhotosAlbum:
            self.log(f"{INFO}\tAcquiring album")
            if INDEX_FILE_NAME not in self.files:
                self.log(f"{ERROR}{self.name}: No {INDEX_FILE_NAME}")
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
                album.add_description(filtered_texts)
                album.add_description([description_title])
            except StopIteration:
                self.log(f"{WARNING}\tNo album description found")

            return album

        def _upload_media(self, album: GooglePhotosAlbum) -> None:
            if HR_FOLDER_NAME not in self.folders:
                self.log(f"{ERROR}{self.name}: No {HR_FOLDER_NAME}/")
                return

            hr_images = [
                f"{self.path}/{HR_FOLDER_NAME}/{f}" for f in get_files(f"{self.path}/{HR_FOLDER_NAME}")]

            if album.mediaItemsCount >= len(hr_images):
                self.log(f"{INFO}\tSkipping")
                return
            self.log(f"{INFO}\tUploading Media")
            inner_pbar = tqdm(desc="MediaItems",
                              total=len(hr_images), position=0)
            for image in hr_images:
                try:
                    image_name = image.split(
                        "/")[-1].replace("hr", "").split(".")[0]
                    media: GooglePhotosMediaItem = list(album.add_media([image])[1])[0]  # noqa
                    with open(f"{self.path}/{IMAGE_PAGES}/{image_name}.html", "r", encoding="utf8") as f:
                        media_html = f.read()
                    media_soup = bs4(media_html, features="html.parser")
                    try:
                        description = media_soup.find_all(
                            "div", {"class": "imagetitle"})[0].contents[0]
                        media.set_description(description)
                    except Exception as e:
                        inner_pbar.write(
                            f"{WARNING}\t{image} has no description!")
                except Exception as e:
                    inner_pbar.write(
                        f"{ERROR}{image} has failed!")
                    inner_pbar.write(f"\t\t{e}")
                inner_pbar.update(1)

        def upload(self) -> None:
            """uploads an album along with relevant data
            """
            try:
                self.log(f"{INFO}Processing {self.name}")
                album: GooglePhotosAlbum = self._setup_album()
                self._upload_media(album)
            except Exception as e:
                self.log(f"{ERROR}Failed to process {self.name}")
                self.log(f"\t\t{e}")
    base_folder = argv[1]
    folder_names = get_directories(base_folder)
    outer_pbar = tqdm(desc="Albums", position=1, total=len(folder_names))
    for album_folder in folder_names:
        Album(f"{base_folder}/{album_folder}", outer_pbar.write).upload()
        outer_pbar.update(1)


def main() -> None:
    logic()


if __name__ == "__main__":
    main()
