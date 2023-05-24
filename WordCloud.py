import os

import numpy             as np 
import pandas            as pd 
import matplotlib.pyplot as plt 

from PIL       import Image 
from wordcloud import WordCloud 
from wordcloud import STOPWORDS
from wordcloud import ImageColorGenerator

%matplotlib inline

def create_word_cloud(contour_width: int = 3, max_font_size: int = 100, max_words: int = 1000, background_color: str = "black", input_text: pd.Series = None, stopwords_list: list[str] = None, image_mask: str = None):
    def define_word_cloud_object():
        stopwords = set(STOPWORDS)
        stopwords.update(list(set(stopwords_list))) if stopwords_list != None else stopwords

        wordcloud_object = WordCloud(
            stopwords        = stopwords,
            max_font_size    = max_font_size,
            background_color = background_color,
            mask             = image_mask_object,
            max_words        = max_words,
            contour_width    = contour_width
        )

        return wordcloud_object
    
    def get_image_mask(image_mask: str):
        mask_image = np.array(Image.open(image_mask))
        trans_mask = np.ndarray((mask_image.shape[0], mask_image.shape[1]), np.int32)

        for i in range(len(mask_image)):
            for j in range(len(mask_image[i])):
                trans_mask[i][j] = (lambda x: 255 if x == 0 else x)(mask_image[i][j])

        return trans_mask

    input_string      = " ".join(text for text in list(input_text))
    image_mask_object = get_image_mask(image_mask) if image_mask != None else image_mask
    wordcloud_object  = define_word_cloud_object()

    plt.figure(figsize = [15, 15])
    plt.imshow(wordcloud_object.generate(input_string), interpolation = "bilinear")
    plt.axis("off")
    plt.show()
    plt.savefig("Sample_figure.png")
    
if __name__ == "__main__":
    df = pd.read_csv(r"C:\Users\User\Downloads\archive\winemag-data-130k-v2.csv")
    create_word_cloud(
        max_words      = 100000,
        input_text     = df["description"], 
        stopwords_list = ["drink", "now", "wine", "flavor", "flavors"]
    )
    
