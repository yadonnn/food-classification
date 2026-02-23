from multiprocessing import Process, Queue
from aihub_downloader import run_download
from image_transformer import transform_consumer
# from bucket_uploader import run_upload

def run_pipeline():

    run_download()
    # run_upload()
    
    print("✅ Pipeline Finished!")

if __name__ == "__main__":
    run_pipeline()
