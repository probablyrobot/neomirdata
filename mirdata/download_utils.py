"""Utilities for downloading from the web."""

import glob
import logging
import os
import shutil
import tarfile
import urllib
import warnings
import zipfile

import chardet
from smart_open import open
from tqdm import tqdm

from mirdata.validate import md5

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class RemoteFileMetadata:
    """The metadata for a remote file

    Attributes:
        filename (str): the remote file's basename
        url (str): the remote file's url
        checksum (str): the remote file's md5 checksum
        destination_dir (str or None): the relative path for where to save the file
        unpack_directories (list or None): list of relative directories. For each directory
            the contents will be moved to destination_dir (or data_home if not provided)

    """

    def __init__(self, filename, url, checksum, destination_dir=None, unpack_directories=None):
        self.filename = filename
        self.url = url
        self.checksum = checksum
        self.destination_dir = destination_dir
        self.unpack_directories = unpack_directories

    def _replace(self, **kwargs):
        """Create a new instance with replaced attributes.

        Args:
            **kwargs: Attributes to replace

        Returns:
            RemoteFileMetadata: A new instance with replaced attributes
        """
        params = {
            "filename": self.filename,
            "url": self.url,
            "checksum": self.checksum,
            "destination_dir": self.destination_dir,
            "unpack_directories": self.unpack_directories,
        }
        params.update(kwargs)
        return RemoteFileMetadata(**params)


def downloader(
    save_dir,
    remotes=None,
    index=None,
    partial_download=None,
    info_message=None,
    force_overwrite=False,
    cleanup=False,
    allow_invalid_checksum=False,
):
    """Download data to `save_dir` and optionally log a message.

    Args:
        save_dir (str):
            The directory to download the data
        remotes (dict or None):
            A dictionary of RemoteFileMetadata tuples of data in zip format.
            If None, there is no data to download
        index (core.Index):
            A mirdata Index class, which may contain a remote index to be downloaded
            or a subset of remotes to download by default.
        partial_download (list or None):
            A list of keys to partially download the remote objects of the download dict.
            If None, all data specified by the index is downloaded
        info_message (str or None):
            A string of info to log when this function is called.
            If None, no string is logged.
        force_overwrite (bool):
            If True, existing files are overwritten by the downloaded files.
        cleanup (bool):
            Whether to delete the zip/tar file after extracting.
        allow_invalid_checksum (bool):
            Allow having an invalid checksum, and whenever this happens prompt a
            warning instead of deleting the files.

    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if not index:
        raise ValueError("Index must be specified.")

    if allow_invalid_checksum:
        cleanup = True

    if cleanup:
        logging.warning(
            "Zip and tar files will be deleted after they are uncompressed. "
            + "If you download this dataset again, it will overwrite existing files, even if force_overwrite=False"
        )

    if index.remote:
        if remotes is None:
            remotes = {}
        remotes["index"] = index.remote

    # if partial download is specified, use it. Otherwise, use the
    # partial download specified by the index.
    partial_download = partial_download if partial_download else index.partial_download

    if remotes is not None:
        if partial_download is not None:
            # check the keys in partial_download are in the download dict
            if not isinstance(partial_download, list) or any(k not in remotes for k in partial_download):
                raise ValueError(
                    f"partial_download must be a list which is a subset of {list(remotes.keys())}, "
                    f"but got {partial_download}"
                )
            objs_to_download = partial_download
            if "index" in remotes:
                objs_to_download.append("index")
        else:
            objs_to_download = list(remotes.keys())

        if "index" in objs_to_download and len(objs_to_download) > 1:
            logging.info(
                f"Downloading {objs_to_download}. Index is being stored in {index.indexes_dir}, "
                f"and the rest of files in {save_dir}"
            )
        elif "index" in objs_to_download and len(objs_to_download) == 1:
            logging.info(f"Downloading {objs_to_download}. Index is being stored in {index.indexes_dir}")
        else:
            logging.info(f"Downloading {objs_to_download} to {save_dir}")

        for k in objs_to_download:
            logging.info(f"[{k}] downloading {remotes[k].filename}")
            extension = os.path.splitext(remotes[k].filename)[-1]
            if ".zip" in extension:
                download_zip_file(
                    remotes[k],
                    save_dir,
                    force_overwrite,
                    cleanup,
                    allow_invalid_checksum,
                )
            elif ".gz" in extension or ".tar" in extension or ".bz2" in extension:
                download_tar_file(
                    remotes[k],
                    save_dir,
                    force_overwrite,
                    cleanup,
                    allow_invalid_checksum,
                )
            else:
                download_from_remote(
                    remotes[k], save_dir, force_overwrite=force_overwrite, allow_invalid_checksum=allow_invalid_checksum
                )

            if remotes[k].unpack_directories:
                for src_dir in remotes[k].unpack_directories:
                    # path to destination directory
                    destination_dir = (
                        os.path.join(save_dir, remotes[k].destination_dir) if remotes[k].destination_dir else save_dir
                    )
                    # path to directory to unpack
                    source_dir = os.path.join(destination_dir, src_dir)

                    if not os.path.exists(source_dir):
                        logging.info(
                            "Data not downloaded, because it probably already exists on your computer. "
                            "Run .validate() to check, or rerun with force_overwrite=True to delete any "
                            "existing files and download from scratch"
                        )
                        return

                    move_directory_contents(source_dir, destination_dir)

    if info_message is not None:
        logging.info(info_message.format(save_dir))


class DownloadProgressBar(tqdm):
    """
    Wrap `tqdm` to show download progress
    """

    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_from_remote(
    remote, save_dir, fix_checksum=False, cleanup=False, force_overwrite=False, allow_invalid_checksum=False
):
    """Download a data file from a remote source and optionally check its checksum.

    Args:
        remote: RemoteFileMetadata object.
        save_dir: Where to save the downloaded.
        fix_checksum: If True, overwrites the saved checksum with the new checksum.
        cleanup: If True, delete the zip file when done.
        force_overwrite: If True, delete existing file if the checksum fails.
        allow_invalid_checksum: If True, invalid checksums are allowed with a warning.

    Returns:
        save_path (str): Path to download.

    Raises:
        IOError: if checksum fails with fix_checksum=False; or if the download is unsuccessful.

    """
    if isinstance(remote, tuple):
        remote_dict = {}
        for i, key in enumerate(["filename", "url", "checksum", "destination_dir", "unpack_directories"]):
            remote_dict[key] = remote[i] if i < len(remote) else None

        remote = RemoteFileMetadata(**remote_dict)

    # Handle destination_dir if specified
    if remote.destination_dir:
        save_dir = os.path.join(save_dir, remote.destination_dir)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, remote.filename)

    # Check if file already exists and has the correct checksum
    if os.path.exists(save_path):
        if remote.checksum is not None and not fix_checksum:
            target_file_md5 = md5(save_path)
            # If the checksum matches, we're done
            if target_file_md5 == remote.checksum:
                logging.info(f"Found {remote.filename} in cache (MD5 hash matches)")
                return save_path
            # If the checksum doesn't match, we report.
            logging.warning(
                f"MD5 hash for {save_path} ({target_file_md5}) does not match expected checksum ({remote.checksum})."
            )
            if not force_overwrite:
                logging.warning(
                    f"Not downloading {save_path} again as it already " "exists and force_overwrite was set to False."
                )
                return save_path

            logging.warning(f"Deleting {save_path} and redownloading...")
            os.remove(save_path)
        else:
            logging.info(f"Found {remote.filename} in cache.")
            return save_path

    # create parent directories if they don't exist
    save_dir = os.path.dirname(save_path)
    if not os.path.exists(save_dir):
        logging.info(f"Creating directory structure: {save_dir}")
        os.makedirs(save_dir, exist_ok=True)

    # download the file
    logging.info(f"Downloading {remote.filename} from {remote.url}")
    try:
        with urllib.request.urlopen(remote.url) as fsrc, open(save_path, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)
    except urllib.request.URLError as e:
        raise OSError(f"Failed to download from {remote.url}: {e.reason if hasattr(e, 'reason') else e}") from e

    # Validate checksum
    if remote.checksum is not None:
        new_checksum = md5(save_path)
        if remote.checksum != new_checksum:
            # Checksum does not match! Either the file downloaded from
            # a broken mirror, or the version on the server is new.
            if fix_checksum:
                logging.info(
                    f"The downloaded file has checksum {new_checksum}, "
                    f"this differs from the expected {remote.checksum}. "
                    "Setting the expected checksum to the new one!"
                )
                warnings.warn(
                    f"The downloaded file has checksum {new_checksum}, "
                    f"this differs from the expected {remote.checksum}. "
                    "Setting the expected checksum to the new one!",
                    stacklevel=2,
                )
                remote = remote._replace(checksum=new_checksum)
            elif allow_invalid_checksum:
                logging.warning(
                    f"The downloaded file has checksum {new_checksum}, "
                    f"this differs from the expected {remote.checksum}. "
                    "Allowing invalid checksum as requested."
                )
                warnings.warn(
                    f"The downloaded file has checksum {new_checksum}, "
                    f"this differs from the expected {remote.checksum}. "
                    "Allowing invalid checksum as requested.",
                    stacklevel=2,
                )
            else:
                # Delete the file
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise OSError(
                    f"The downloaded file has checksum {new_checksum}, "
                    f"this differs from the expected {remote.checksum}. "
                    "Please retry download."
                )

    return save_path


def download_zip_file(zip_remote, save_dir, force_overwrite, cleanup, allow_invalid_checksum):
    """Download and unzip a zip file.

    Args:
        zip_remote (RemoteFileMetadata):
            Object containing download information
        save_dir (str):
            Path to save downloaded file
        force_overwrite (bool):
            If True, overwrites existing files
        cleanup (bool):
            If True, remove zipfile after unziping
        allow_invalid_checksum (bool):
            If True, invalid checksums are allowed with a warning.

    """
    zip_download_path = download_from_remote(
        zip_remote, save_dir, force_overwrite=force_overwrite, allow_invalid_checksum=allow_invalid_checksum
    )
    unzip(zip_download_path, cleanup=cleanup)


def extractall_unicode(zfile, out_dir):
    """Extract all files inside a zip archive to a output directory.

    In comparison to the zipfile, it checks for correct file name encoding

    Args:
        zfile (obj): Zip file object created with zipfile.ZipFile
        out_dir (str): Output folder

    """
    zip_filename_utf8_flag = 0x800

    for m in zfile.infolist():
        data = zfile.read(m)  # extract zipped data into memory

        filename = m.filename

        # if block to deal with irmas and good-sounds archives
        # check if the zip archive does not have the encoding info set
        # encode-decode filename only if it's different than the original name
        if (m.flag_bits & zip_filename_utf8_flag == 0) and filename.encode("cp437").decode(errors="ignore") != filename:
            filename_bytes = filename.encode("cp437")
            if filename_bytes.decode("utf-8", "replace") != filename_bytes.decode(errors="ignore"):
                guessed_encoding = chardet.detect(filename_bytes)["encoding"] or "utf8"
                filename = filename_bytes.decode(guessed_encoding, "replace")
            else:
                filename = filename_bytes.decode("utf-8", "replace")

        disk_file_name = os.path.join(out_dir, filename)

        dir_name = os.path.dirname(disk_file_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        if not os.path.isdir(disk_file_name):
            with open(disk_file_name, "wb") as fd:
                fd.write(data)


def unzip(zip_path, cleanup):
    """Unzip a zip file inside it's current directory.

    Args:
        zip_path (str): Path to zip file
        cleanup (bool): If True, remove zipfile after unzipping

    """
    zfile = zipfile.ZipFile(zip_path, "r")
    extractall_unicode(zfile, os.path.dirname(zip_path))
    zfile.close()
    if cleanup:
        os.remove(zip_path)


def download_tar_file(tar_remote, save_dir, force_overwrite, cleanup, allow_invalid_checksum):
    """Download and untar a tar file.

    Args:
        tar_remote (RemoteFileMetadata): Object containing download information
        save_dir (str): Path to save downloaded file
        force_overwrite (bool): If True, overwrites existing files
        cleanup (bool): If True, remove tarfile after untarring
        allow_invalid_checksum (bool): If True, invalid checksums are allowed with a warning.

    """
    tar_download_path = download_from_remote(
        tar_remote, save_dir, force_overwrite=force_overwrite, allow_invalid_checksum=allow_invalid_checksum
    )
    untar(tar_download_path, cleanup=cleanup)


def untar(tar_path, cleanup):
    """Untar a tar file inside it's current directory.

    Args:
        tar_path (str): Path to tar file
        cleanup (bool): If True, remove tarfile after untarring

    """
    tfile = tarfile.open(tar_path, "r")
    tfile.extractall(os.path.dirname(tar_path))
    tfile.close()
    if cleanup:
        os.remove(tar_path)


def move_directory_contents(source_dir, target_dir):
    """Move the contents of source_dir into target_dir, and delete source_dir

    Args:
        source_dir (str): path to source directory
        target_dir (str): path to target directory

    """
    directory_contents = glob.glob(os.path.join(source_dir, "*"))
    for fpath in directory_contents:
        target_path = os.path.join(target_dir, os.path.basename(fpath))
        if os.path.exists(target_path):
            logging.info(f"{target_path} already exists. Run with force_overwrite=True to download from scratch")
            continue
        shutil.move(fpath, target_dir)

    shutil.rmtree(source_dir)
