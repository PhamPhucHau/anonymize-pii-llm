import os

class Logger:
    def __init__(self):
        pass

    def save_text_to_file(folder_path, file_name, text_content):
        """
        Creates a folder if it does not exist and saves text content to a specified file within it.

        Args:
            folder_path (str): Path to the folder where the file will be saved.
            file_name (str): Name of the file to create or overwrite.
            text_content (str): Text content to write to the file.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        try:
            # Create folder if it does not exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Construct full file path
            file_path = os.path.join(folder_path, file_name)

            # Write text content to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text_content)

            return True

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return False

    
