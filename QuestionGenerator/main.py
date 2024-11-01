from qcm_generator import QCMGenerator

def main():
    md_path = r'/home/irvin/Documents/Obsidian/Osyna/Learning Center/Définitions'
    generator = QCMGenerator(
        model="llama3.1:latest",
        embedding_model="nomic-embed-text"
    )
    generator.process_folder(md_path)

if __name__ == '__main__':
    main()


