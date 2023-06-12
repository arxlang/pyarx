import os
import sys
import tempfile

INPUT_FROM_STDIN = False
INPUT_FILE = ""
EOF = sys.maxunicode + 1


def get_char() -> int:
    """
    Get a char from the buffer or from the default input.

    Returns
    -------
    int
        An integer representation of a char from the buffer.
    """
    if INPUT_FROM_STDIN:
        return ord(sys.stdin.read(1))
    return input_buffer.get()


def file_to_buffer(filename: str) -> None:
    """
    Copy the file content to the buffer.

    Parameters
    ----------
    filename : str
        The name of the file to be copied to the buffer.
    """
    with open(filename, "r") as arxfile:
        input_buffer.clear()
        for line in arxfile:
            input_buffer.write(line + "\n")


def string_to_buffer(value: str) -> None:
    """
    Copy the given string to the buffer.

    Parameters
    ----------
    value : str
        The string to be copied to the buffer.
    """
    input_buffer.clear()
    input_buffer.str("")
    input_buffer.write(value + "\n" + chr(EOF))


def load_input_to_buffer() -> None:
    """
    Load the content file or the standard input to the buffer.
    """
    if INPUT_FILE != "":
        input_file_path = os.path.abspath(INPUT_FILE)
        file_to_buffer(input_file_path)
    else:
        file_content = sys.stdin.read().strip()

        if file_content != "":
            string_to_buffer(file_content)


class ArxFile:
    @staticmethod
    def create_tmp_file(content: str) -> str:
        """
        Create a temporary file with the given content.

        Parameters
        ----------
        content : str
            The content of the temporary file.

        Returns
        -------
        str
            The name of the created temporary file.
        """
        # Create a temporary file.
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(content.encode())

        # Rename the temporary file with the .cpp extension.
        filename = tmpfile.name
        filename_ext = filename + ".cpp"
        os.rename(filename, filename_ext)

        return filename_ext

    @staticmethod
    def delete_file(filename: str) -> int:
        """
        Delete the specified file.

        Parameters
        ----------
        filename : str
            The name of the file to be deleted.

        Returns
        -------
        int
            Returns 0 on success, or -1 on failure.
        """
        try:
            os.remove(filename)
            return 0
        except OSError:
            return -1
