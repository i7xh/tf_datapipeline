import _init_paths
import os
import tensorflow as tf
from data import inception_preprocessing

SPLITS_TO_SIZES = {'train': 3320, 'validation': 350}
_FILE_PATTERN = 'flowers_%s_'
_NUM_SHARDS = 5

def read_and_decode(filename_queue):

    reader = tf.TFRecordReader()
    _, serialized_example = reader.read(filename_queue)

    features = tf.parse_single_example(
        serialized_example,
        # Defaults are not specified since both keys are required.
        features={
            'image/encoded': tf.FixedLenFeature([], tf.string),
            'image/class/label': tf.FixedLenFeature([], tf.int64),
            'image/height': tf.FixedLenFeature([], tf.int64),
            'image/width': tf.FixedLenFeature([], tf.int64),
        })

    label = tf.cast(features['image/class/label'], tf.int32)
    height = tf.cast(features['image/height'], tf.int32)
    width = tf.cast(features['image/width'], tf.int32)

    image = tf.image.decode_jpeg(features['image/encoded'])

    image_shape = tf.stack([height, width, 3])
    image = tf.reshape(image, image_shape)

    #image = tf.Print(image,[tf.size(image)],"image:")

    return image, label

def inputs(split_name, batch_size, dataset_dir, num_epochs=1,
           width=299, height=299, is_training=True):

    filename_list = []

    if split_name not in SPLITS_TO_SIZES:
        raise ValueError('split name %s was not recognized.' % split_name)

    for i in range(_NUM_SHARDS):
        filename_list.append(os.path.join(dataset_dir,  'flowers_%s_%05d-of-%05d.tfrecord' % (split_name, i, _NUM_SHARDS)))

    with tf.name_scope('input'):
        filename_queue = tf.train.string_input_producer(filename_list, num_epochs=num_epochs)
        #filename_queue = tf.train.string_input_producer(filename_list, num_epochs=num_epochs)

        image, label = read_and_decode(filename_queue)

        image = inception_preprocessing.preprocess_image(image, height, width,is_training)

        print ("batch queue config", batch_size, 50*batch_size, 20*batch_size)
        images, labels = tf.train.shuffle_batch(
            [image, label], batch_size=batch_size, num_threads=4,
            capacity=50*batch_size, allow_smaller_final_batch = True, min_after_dequeue=20*batch_size )

    return images, labels