def read_file(file_path):
    """Reads the content of a file and returns it as a string."""
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    """Writes the given content to a file."""
    with open(file_path, 'w') as file:
        file.write(content)

def file_exists(file_path):
    """Checks if a file exists at the given path."""
    import os
    return os.path.isfile(file_path)

def delete_file(file_path):
    """Deletes the file at the given path if it exists."""
    import os
    if file_exists(file_path):
        os.remove(file_path)

def get_file_extension(file_path):
    """Returns the file extension of the given file path."""
    import os
    return os.path.splitext(file_path)[1]