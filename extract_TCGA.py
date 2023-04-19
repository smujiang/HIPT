# Import the relevant libraries from this module
import openslide
from wsitools.tissue_detection.tissue_detector import TissueDetector
from wsitools.patch_extraction.patch_extractor import ExtractorParameters, PatchExtractor
import multiprocessing
import os
import glob

# Define some run parameters
num_processors = 20  # Number of processes that can be running at once


def get_TCGA_wsi_fn_list(data_dir):
    dirs = list(filter(os.path.isdir, glob.glob(os.path.join(data_dir, "*"))))
    wsi_fn_list = []
    for d in dirs:
        wsi_fn = glob.glob(os.path.join(data_dir, d, "*.svs"))
        wsi_obj = openslide.OpenSlide(wsi_fn[0])
        xsize = float(wsi_obj.properties["openslide.mpp-x"])
        print(wsi_fn)
        if xsize > 0.26:
            print("\t discard Low resolution")
        else:
            wsi_fn_list.append(wsi_fn[0])
    return wsi_fn_list


data_dir = "/grand/projects/gpu_hack/smujiang/data"
output_dir = "/grand/projects/gpu_hack/smujiang/img_patches_256_20x"  # Define an output directory
log_dir = "/grand/projects/gpu_hack/smujiang/img_patches_256_20x/logs"
wsi_fn_list = get_TCGA_wsi_fn_list(data_dir)
print(wsi_fn_list)

# Define the parameters for Patch Extraction, including generating an thumbnail from which to traverse over to find
# tissue.
parameters = ExtractorParameters(output_dir,  # Where the patches should be extracted to
                                 save_format='.png',  # Can be '.jpg', '.png', or '.tfrecord'
                                 sample_cnt=-1,  # Limit the number of patches to extract (-1 == all patches)
                                 patch_size=512,  # Size of patches to extract (Height & Width)
                                 patch_rescale_to=256,
                                 stride=512,
                                 rescale_rate=128,  # Fold size to scale the thumbnail to (for faster processing)
                                 log_dir=log_dir,
                                 patch_filter_by_area=0.5,  # Amount of tissue that should be present in a patch
                                 with_anno=True,  # If true, you need to supply an additional XML file
                                 extract_layer=0  # OpenSlide Level
                                 )

# Choose a method for detecting tissue in thumbnail image
tissue_detector = TissueDetector("LAB_Threshold",  # Can be LAB_Threshold or GNB
                                 threshold=85,
                                 # Number from 1-255, anything less than this number means there is tissue
                                 training_files=None  # Training file for GNB-based detection
                                 )

# Create the extractor object
patch_extractor = PatchExtractor(tissue_detector,
                                 parameters,
                                 feature_map=None,  # See note below
                                 annotations=None  # Object of Annotation Class (see other note below)
                                 )

if __name__ == "__main__":
    # Run the extraction process
    multiprocessing.set_start_method('spawn')
    pool = multiprocessing.Pool(processes=num_processors)
    pool.map(patch_extractor.extract, wsi_fn_list)
