# -*- coding: utf-8 -*-
"""AutomateTaggingImageClothes_update.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LBiip2IJPSuDgjwKy6e3YedoMh6VCtDP
"""

import numpy as np
import pandas as pd
import os 
import glob
import matplotlib.pyplot as plt
from logging import error
from sklearn.utils import shuffle
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from PIL import Image
from keras.layers.convolutional import Conv2D
from keras.models import Sequential,Model,load_model
from tensorflow.keras.optimizers import SGD
from keras.layers import BatchNormalization, Lambda, Input, Dense, Convolution2D, MaxPooling2D, AveragePooling2D, ZeroPadding2D, Dropout, Flatten, merge, Reshape, Activation
from keras.layers.merge import Concatenate
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint
from keras.layers import Input
from tensorflow.keras.optimizers import Adam
import numpy as np

dataset_folder_name = "E:\Crawler\change\data"
train_test_split = 0.8
image_width = image_height = 100

#tag predict 
os.chdir("E:\Crawler\change\data")
dataset_dict = {
    'category_id' : {
        0:'quần dài', 
        1:'quần short', 
        2:'váy liền',
        3:'áo phông', 
        4:'áo sơ mi',
        5:'áo nỉ',
        6:'áo khoác' 
    },
}


dataset_dict['category_alias'] = dict((g,i) for i, g in dataset_dict['category_id'].items())
# extracting the data from the dataset
def parse_dataset(dataset_path):

  """ 
  Use to extract information about our dataset. It does interate over all images 
  and return a DataFrame with the data (category, color, gender, isAdult) of all files.
  """
  def parse_into_from_file(path):
    """
    Parse information from a single file
    """
    try:
      filename = os.path.split(path)[1]
      filename = os.path.splitext(filename)[0]
      filename = filename.split(' ')[0]
      listname = filename.split('_')
      category,color,gender,isAdult = listname[0], listname[1], listname[2], listname[3]
      return dataset_dict['category_id'][int(category)], listname[0]
    except Exception as ex:
      pass
  files = os.listdir(dataset_path)
  records = []
  for file in files:
    info = parse_into_from_file(file)
    records.append(info)

  df = pd.DataFrame(records)
  df['file'] = files
  df.columns = ['category', 'category_id',  'file']

  return df


df = parse_dataset(dataset_folder_name)
df.head()

# data visualization
import plotly.graph_objects as go

def plot_distribution(pd_series):
  labels = pd_series.value_counts().index.tolist()
  counts = pd_series.value_counts().values.tolist()

  pie_plot = go.Pie(values=counts, labels=labels, hole=0.5)
  fig = go.Figure(data = [pie_plot])
  fig.update_layout(title_text = 'Distribution for %s' %pd_series.name)

  fig.show()

plot_distribution(df['category'])


# data generator
"""
In order to input data to our Keras multi-output model, we will create a helper 
object to wr=ork as a data generator for out dataset. 
"""

#index 
print("starting generate image ")

print("starting get index")
p = np.random.permutation(len(df))
train_up_to = int(len(df) * train_test_split)
train_idx = p[:train_up_to]
test_idx = p[train_up_to:]

train_up_to = int(train_up_to * train_test_split)
train_idx, valid_idx = train_idx[:train_up_to], train_idx[train_up_to:]



print("starting get array image")
def generate_images(image_idx):
    """
    Using to generate a batch with images when training/ testing/ validating our Keras model
    """

    images, categories= [],  []
    for idx in image_idx:
      cloth = df.iloc[idx]          
      category = cloth['category_id']
      file = cloth['file']

      im = Image.open(file).convert('LA')
      im = im.resize((image_width, image_height))
      im = np.array(im) / 255.0
      try:
        if int(category) <= max(dataset_dict['category_id']) and int(category) >= 0:
          categories.append(to_categorical(category,len(dataset_dict['category_id'])).astype("uint8"))
          images.append(im)
        else :
          continue
      except Exception as err:
        print(error)
    return shuffle(images, categories)

print("starting with valid dataset")
print(len(valid_idx))
validX, validY = generate_images(valid_idx)

print("starting with training dataset")
print(len(train_idx))
trainX, trainY = generate_images(train_idx)
print("starting with test dataset")
print(len(test_idx))
testX, testY = generate_images(test_idx)


trainX = np.array(trainX)
trainY = np.array(trainY)

testX = np.array(testX)
testY = np.array(testY)

validX = np.array(validX)
validY = np.array(validY)

model = Sequential()
model.add(Conv2D(32, (3,3), input_shape = (image_height,image_width,2), padding = "same"))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Dropout(0.25))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Conv2D(64, (3,3), padding = "same"))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Dropout(0.25))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Conv2D(128, (3,3), padding = "same"))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Dropout(0.4))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Flatten())
model.add(Dense(128))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Dropout(0.3))
model.add(Activation("relu"))
model.add(BatchNormalization())

model.add(Dense(7))
model.add(Activation("softmax"))

model.summary()

learning_rate = 0.01
epochs = 100

opt = Adam(learning_rate = learning_rate)
model.compile(loss= "mean_squared_error",
               optimizer = 'rmsprop',
               metrics = ['accuracy'])

from tensorflow.python.util import nest


# aug = ImageDataGenerator(rotation_range=0.18, zoom_range=0.15, width_shift_range= 0.2, height_shift_range=0.2, horizontal_flip=True, input_shape=(image_height, image_width, 2))
batch_size = 64
valid_batch_size = 64

print("starting training")
history = model.fit(
    # aug.flow(trainX, trainY, batch_size=batch_size),
    trainX, trainY,
    steps_per_epoch=len(train_idx)//batch_size,
    batch_size=batch_size, 
    epochs=epochs,
    validation_data=(validX, validY),
    validation_steps=len(valid_idx)//valid_batch_size,
    verbose = 1)
model.save("../category.h5")
# accuracy for category
# plt.clf()
# fig = go.Figure()
# fig.add_trace(go.Scatter(
#     y=history.history('output_race'),
#     name='Train'
# ))
# fig.add_trace(go.Scatter(
#     y=history.history('val_output_race'),
#     name='Valid'
# ))
# fig.update_layout(
#     height=500,
#     width=700,
#     title='Accuracy for race feature',
#     xaxis_title='Epoch',
#     yaxis_title='Accuracy'
# )
# fig.show()

# accuracy for color
# plt.clf()
# fig = go.Figure()
# fig.add_trace(go.Scatter(
#     y=history.history('color_output_race'),
#     name='Train'
# ))
# fig.add_trace(go.Scatter(
#     y=history.history('val_color_output_race'),
#     name='Valid'
# ))
# fig.update_layout(
#     height=500,
#     width=700,
#     title='Accuracy for color feature',
#     xaxis_title='Epoch',
#     yaxis_title='Accuracy'
# )
# fig.show()