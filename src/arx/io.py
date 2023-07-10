"""Module for handling the IO used by the compiler."""
import os
import sys
import tempfile


class ArxBuffer:
    """ArxBuffer gathers function for handle the system buffer."""

    buffer: str = ""
    position: int = 0

    def __init__(self) -> None:
        """Initialize ArxBuffer instance."""
        self.clean()

    def clean(self) -> None:
        """Clean the buffer content."""
        self.position = 0
        self.buffer = ""

    def write(self, text: str) -> None:
        """Write the given text to the buffer."""
        self.buffer += text
        self.position = 0

    def read(self) -> str:
        """Read the buffer content."""
        try:
            i = self.position
            self.position += 1
            return self.buffer[i]
        except IndexError:
            return ""


class ArxIO:
    """Arx class for Input and Output operations."""

    INPUT_FROM_STDIN: bool = False
    INPUT_FILE: str = ""
    EOF: int = sys.maxunicode + 1
    buffer: ArxBuffer = ArxBuffer()

    @classmethod
    def get_char(cls) -> str:
        """
        Get a char from the buffer or from the default input.

        Returns
        -------
        str
            A char from the buffer.
        """
        if cls.INPUT_FROM_STDIN:
            return sys.stdin.read(1)
        return cls.buffer.read()

    @classmethod
    def file_to_buffer(cls, filename: str) -> None:
        """
        Copy the file content to the buffer.

        Parameters
        ----------
        filename : str
            The name of the file to be copied to the buffer.
        """
        with open(filename, "r") as arxfile:
            cls.buffer.clean()
            for line in arxfile:
                cls.buffer.write(line + "\n")

    @classmethod
    def string_to_buffer(cls, value: str) -> None:
        """
        Copy the given string to the buffer.

        Parameters
        ----------
        value : str
            The string to be copied to the buffer.
        """
        cls.buffer.clean()
        cls.buffer.write(value)

    @classmethod
    def load_input_to_buffer(cls) -> None:
        """Load the content file or the standard input to the buffer."""
        if cls.INPUT_FILE:
            input_file_path = os.path.abspath(cls.INPUT_FILE)
            cls.file_to_buffer(input_file_path)
            return

        file_content = sys.stdin.read().strip()
        if file_content:
            cls.string_to_buffer(file_content)


class ArxFile:
    """ArxFile gathers function to handle files."""

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
