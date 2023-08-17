import sys
from typing import Generator, Optional
from pathlib import Path
from utils import get_directories, get_files, t_dict, t_list, INFO, WARNING, ERROR
from bs4 import BeautifulSoup as bs4
from bs4.element import Tag
from gp_wrapper import GooglePhotos, Album, MediaItem, NewMediaItem, SimpleMediaItem, \
    MEDIA_ITEM_BATCH_CREATE_MAXIMUM_IDS
from progress_bar_pool import ProgressBarPool


class LocalAlbum:
    """a wrapper class to simply uploading the data
    """

    def __init__(self, gp: GooglePhotos, path: str, p: ProgressBarPool, index_file_name: str = "index.html",
                 hr_folder_name: str = "hrimages", image_pages_folder: str = "imagepages") -> None:
        self.gp = gp
        self.existing_album: t_dict[str, Album] = {
            a.title: a for a in Album.all_albums(self.gp)}
        self.path = path
        self.files = get_files(path)
        self.folders = get_directories(path)
        self.name = Path(self.path).stem
        self.p = p
        self.index_file_name = index_file_name
        self.hr_folder_name = hr_folder_name
        self.image_pages_folder = image_pages_folder
        self.album: Album

    def _setup_album(self) -> Album:
        self.p.write(f"{INFO}\tAcquiring album")
        if self.index_file_name not in self.files:
            self.p.write(f"{ERROR}{self.name}: No {self.index_file_name}")
            raise ValueError(
                f"Can't process album as there is no '{self.index_file_name}' file")
        with open(f"{self.path}/{self.index_file_name}", "r", encoding="utf8") as f:
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

    def _create_media_items(self, album: Album) -> Optional["t_list[NewMediaItem]"]:
        if self.hr_folder_name not in self.folders:
            self.p.write(f"{ERROR}{self.name}: No {self.hr_folder_name}/")
            return None

        hr_images = [f"{self.path}/{self.hr_folder_name}/{f}" for f in
                     get_files(f"{self.path}/{self.hr_folder_name}")]  # noqa

        if album.mediaItemsCount >= len(hr_images):
            self.p.write(f"{INFO}\tAlready has all media. Skipping")
            return None

        self.p.write(f"{INFO}\tUploading Media")
        self.p.bars[1].total = len(hr_images)

        items: t_list[NewMediaItem] = []
        for i, path in enumerate(hr_images):
            image_name = path.split("/")[-1].replace("hr", "").split(".")[0]  # noqa
            with open(f"{self.path}/{self.image_pages_folder}/{image_name}.html", "r", encoding="utf8") as f:
                media_html = f.read()
            media_soup = bs4(media_html, features="html.parser")
            description: str = ""
            try:
                description = media_soup.find_all("div", {"class": "imagetitle"})[0].contents[0]  # noqa
                if not isinstance(description, str):
                    if isinstance(description, Tag):
                        description = description.contents[0]
                    else:
                        self.p.write(
                            f"{ERROR}Unhandled description type {type(description)}")
            except Exception as e:  # pylint: disable=broad-exception-caught
                self.p.write(f"{WARNING}\t{image_name} has no description!")  # noqa
            if not sys.stdout.isatty():
                self.p.bars[0].desc = f"Uploading {i}/{len(hr_images)}"
            token = MediaItem.upload_media(self.gp, path, pbar=self.p.bars[0])
            item = NewMediaItem(description, SimpleMediaItem(token, image_name))  # noqa
            items.append(item)
            self.p.bars[1].update()

        return items

    def _attach_media(self, album: Album, items: "t_list[NewMediaItem]") -> None:
        self.p.write(f"{INFO}Attaching uploaded media to account+album")
        batches: t_list[t_list[NewMediaItem]] = []
        batch: t_list[NewMediaItem] = []
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
        # try:
        self.p.write(f"{INFO}Processing {self.name}")
        self.album: Album = self._setup_album()
        media_items = self._create_media_items(self.album)
        if media_items:
            self._attach_media(self.album, media_items)
        # except Exception as e:  # pylint: disable=broad-exception-caught
        #     self.p.write(f"{ERROR}Failed to process {self.name}")
        #     self.p.write(f"\t\t{e}")
