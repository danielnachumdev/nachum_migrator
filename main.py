from typing import Generator, Optional
from sys import argv
from pathlib import Path
from danielutils import get_directories, get_files, ColoredText
from bs4 import BeautifulSoup as bs4
from tqdm import tqdm
from gp_wrapper import GooglePhotos, Album, MediaItem, NewMediaItem, SimpleMediaItem,\
    MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS
INDEX_FILE_NAME = "index.html"
HR_FOLDER_NAME = "hrimages"
IMAGE_PAGES = "imagepages"
_INFO = ColoredText.yellow("INFO")+":"
_WARNING = ColoredText.orange("WARNING")+":"
_ERROR = ColoredText.red("ERROR")+":"
MARGIN = len(_WARNING)+4
INFO, WARNING, ERROR = [s.ljust(MARGIN) for s in [_INFO, _WARNING, _ERROR]]


class ProgressBarPool:
    def __init__(self, num_of_bars: int = 1, *, global_options: Optional[dict] = None, individual_options: Optional[list[Optional[dict]]] = None) -> None:
        self.bars: list[tqdm] = []
        if global_options is None:
            global_options = {}
        if individual_options is None:
            individual_options = [{} for _ in range(num_of_bars)]
        if len(individual_options) != num_of_bars:
            raise ValueError("")
        for i in range(num_of_bars):
            if individual_options[i] is None:
                individual_options[i] = {}
        for i in range(num_of_bars):
            final_options: dict = global_options.copy()
            final_options.update(individual_options[i])  # type:ignore
            if "desc" not in final_options:
                final_options["desc"] = f"pbar {i}"
            t = tqdm(
                position=i,
                **final_options
            )
            self.bars.append(t)

    def write(self, *args, sep=" ", end="\n") -> None:
        self.bars[0].write(sep.join((str(a) for a in args)), end=end)


class LocalAlbum:
    """a wrapper class to simply uploading the data
    """

    def __init__(self, gp: GooglePhotos, path: str, p: ProgressBarPool) -> None:
        self.gp = gp
        self.existing_album: dict[str, Album] = {
            a.title: a for a in Album.all_albums(self.gp)}
        self.path = path
        self.files = get_files(path)
        self.folders = get_directories(path)
        self.name = Path(self.path).stem
        self.p = p

    def _setup_album(self) -> Album:
        self.p.write(f"{INFO}\tAcquiring album")
        if INDEX_FILE_NAME not in self.files:
            self.p.write(f"{ERROR}{self.name}: No {INDEX_FILE_NAME}")
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

        if album_title not in self.existing_album:
            album = Album.create(self.gp, album_title)
        else:
            return self.existing_album[album_title]

        try:
            description_title = next(filtered_texts)
            album.add_text(filtered_texts)
            album.add_text([description_title])
        except StopIteration:
            self.p.write(f"{WARNING}\tNo album description found")

        return album

    def _upload_media(self, album: Album) -> Optional[list[NewMediaItem]]:
        if HR_FOLDER_NAME not in self.folders:
            self.p.write(f"{ERROR}{self.name}: No {HR_FOLDER_NAME}/")
            return None

        hr_images = [
            f"{self.path}/{HR_FOLDER_NAME}/{f}" for f in get_files(f"{self.path}/{HR_FOLDER_NAME}")]

        if album.mediaItemsCount >= len(hr_images):
            self.p.write(f"{INFO}\tSkipping")
            return None

        self.p.write(f"{INFO}\tUploading Media")
        self.p.bars[1].total = len(hr_images)

        items: list[NewMediaItem] = []
        for path in hr_images:
            image_name = path.split("/")[-1].replace("hr", "").split(".")[0]  # noqa
            with open(f"{self.path}/{IMAGE_PAGES}/{image_name}.html", "r", encoding="utf8") as f:
                media_html = f.read()
            media_soup = bs4(media_html, features="html.parser")
            description: str = ""
            try:
                description = media_soup.find_all("div", {"class": "imagetitle"})[0].contents[0]  # noqa
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.p.write(f"{WARNING}\t{image_name} has no description!")  # noqa
            token = MediaItem.upload_media(self.gp, path, tqdm=self.p.bars[0])
            item = NewMediaItem(description, SimpleMediaItem(token, image_name))  # noqa
            items.append(item)
            self.p.bars[1].update()

        return items

    def _attach_media(self, album: Album, items: list[NewMediaItem]) -> None:
        batches: list[list[NewMediaItem]] = []
        batch: list[NewMediaItem] = []
        for item in items:
            if len(batch) >= MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS:
                batches.append(batch)
                batch = []
            batch.append(item)
        batches.append(batch)

        for batch in batches:
            MediaItem.batchCreate(self.gp, batch, album.id)

    def upload(self) -> None:
        """uploads an album along with relevant data
        """
        try:
            self.p.write(f"{INFO}Processing {self.name}")
            album: Album = self._setup_album()
            media_items = self._upload_media(album)
            if media_items:
                self._attach_media(album, media_items)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.p.write(f"{ERROR}Failed to process {self.name}")
            self.p.write(f"\t\t{e}")


def main() -> None:
    base_folder = argv[1]
    folder_names = get_directories(base_folder)
    p = ProgressBarPool(
        3,
        global_options=dict(
        ),
        individual_options=[
            dict(
                desc="Uploading",
                leave=False,
            ),
            dict(
                desc="MediaItems",
                leave=False
            ),
            dict(
                desc="Albums",
                total=len(folder_names)
            )
        ]
    )
    p.write(f"{INFO}Initializing GooglePhotos")
    gp = GooglePhotos()
    for album_folder in folder_names[1:]:
        LocalAlbum(gp, f"{base_folder}/{album_folder}", p).upload()
        p.bars[1].reset()
        p.bars[2].update()


if __name__ == "__main__":
    main()
