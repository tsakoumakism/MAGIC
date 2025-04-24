import arxiv
import pdfplumber
import os, shutil

client = arxiv.Client()
downloaded_papers_dir_name = 'downloaded_papers'
downloaded_papers_path = './'+downloaded_papers_dir_name

def search_papers(search_terms, max_results=5):

    print("-----------------------SEARCH TERMS -----------------")
    print(search_terms)
    search = arxiv.Search(
        query=search_terms,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = client.results(search)
    folder_handling()
    print("-----------------------PAPERS-----------------")
    #'''
    for result in results:
        print(result.title)
        print(result.pdf_url)
        result.download_pdf(dirpath=downloaded_papers_path, filename=f"{result.get_short_id()}.pdf")
    #'''

def read_pdfs():

    pdf_directory = downloaded_papers_path
    pdf_texts = []

    for filename in os.listdir(pdf_directory): # Iterate over all files in the specified directory
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(pdf_directory, filename)
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = ''
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                    pdf_texts.append(text)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    return pdf_texts

def query_formatting(search_terms):
    formatted_search_terms = search_terms.replace(',', ' AND')
    query = "ti:({})".format(formatted_search_terms)
    return query

#if folder exists, empty it, else create it
def folder_handling():
    if os.path.isdir(downloaded_papers_path):
        print('Folder exists------------')
        folder = downloaded_papers_path
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
    else:
        try:
            os.mkdir(downloaded_papers_dir_name)
            print(f"Directory '{downloaded_papers_dir_name}' created successfully.")
        except FileExistsError:
            print(f"Directory '{downloaded_papers_dir_name}' already exists.")
        except PermissionError:
            print(f"Permission denied: Unable to create '{downloaded_papers_dir_name}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

#terms = query_formatting('resistance, training')
terms = query_formatting('electron, proton')
search_papers(terms)

#search_papers('all:(electron AND proton)')
