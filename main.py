#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    # load model graph from saved .db file
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    model_graph = tf.get_default_graph()
    op = sess.graph.get_operations()
    assert model_graph is not None
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tensors = (
        model_graph.get_tensor_by_name(vgg_input_tensor_name),
        model_graph.get_tensor_by_name(vgg_keep_prob_tensor_name),
        model_graph.get_tensor_by_name(vgg_layer3_out_tensor_name),
        model_graph.get_tensor_by_name(vgg_layer4_out_tensor_name),
        model_graph.get_tensor_by_name(vgg_layer7_out_tensor_name),
    )
    print (type(tensors[0]))

    return tensors
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    # apply first FC and skip layer
    l2_reg = 0.0001
    print("Shape", tf.Print(vgg_layer7_out, [vgg_layer7_out]))
    fcn_8 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, strides=(1,1), padding='same',
                             kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=l2_reg))
    fcn_8_2_x = tf.layers.conv2d_transpose(fcn_8, vgg_layer4_out.get_shape()[3], 4, strides=(2,2), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=l2_reg))
    fuse_1 = tf.add(fcn_8_2_x, vgg_layer4_out)
    fcn_9_2_x = tf.layers.conv2d_transpose(fuse_1, vgg_layer3_out.get_shape()[3], 4, strides=(2,2), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=l2_reg))
    print("Shape", tf.Print(fcn_8_2_x, [fcn_8_2_x]))
    fuse_2 = tf.add(fcn_9_2_x, vgg_layer3_out)
    final_layer = tf.layers.conv2d_transpose(fuse_2, num_classes, 16, strides=(8,8), padding='same',
                                           kernel_regularizer=tf.contrib.layers.l2_regularizer(scale=l2_reg))
    return tf.reshape(final_layer, (-1, 160, 576, num_classes))
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=correct_label))
    reg_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
    losses = cross_entropy_loss + sum(reg_losses)
    optimizer = tf.train.AdamOptimizer(learning_rate)
    train_op = optimizer.minimize(losses)
    return logits, train_op, losses
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op,
             cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.
        Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    sess.run(tf.global_variables_initializer())
    for i in range(epochs):
        print ("Epoch %d ....." % i)
        # iterate for each epoch
        generator = get_batches_fn(batch_size)
        for next_input, next_label in generator:
            _, acc = sess.run([train_op, cross_entropy_loss], feed_dict={
                                learning_rate: 0.0005,
                                input_image: next_input,
                                correct_label: next_label,
                                keep_prob: 0.6
                            })
            print ("Loss: ", acc)


tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)  # KITTI dataset uses 160x576 images
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)
    epochs = 20
    batch_size = 32
    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/
    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        tensors = load_vgg(sess, vgg_path)
        network = layers(tensors[2], tensors[3], tensors[4], num_classes)

        # TODO: Train NN using the train_nn function
        learning_rate = tf.placeholder(tf.float32, name="learning_rate")
        correct_label = tf.placeholder(tf.int32, [None, image_shape[0], image_shape[1], num_classes], name="correct_label")
        logits, train_op, loss = optimize(network, correct_label, learning_rate, num_classes)
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, loss, tensors[0], correct_label, tensors[1], learning_rate)
        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, tensors[1], tensors[0])

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
