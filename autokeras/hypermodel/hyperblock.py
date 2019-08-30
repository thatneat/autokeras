from tensorflow.python.util import nest

from autokeras.hypermodel import block
from autokeras.hypermodel import head as head_module
from autokeras.hypermodel import node
from autokeras.hypermodel import preprocessor


class HyperBlock(block.Block):
    """HyperBlock uses hyperparameters to decide inner Block graph.

    A HyperBlock should be build into connected Blocks instead of individual Keras
    layers. The main purpose of creating the HyperBlock class is for the ease of
    parsing the graph for preprocessors. The graph would be hard to parse if a Block,
    whose inner structure is decided by hyperparameters dynamically, contains both
    preprocessors and Keras layers.

    When the preprocessing layers of Keras are ready to cover all the preprocessors
    in AutoKeras, the preprocessors should be handled by the Keras Model. The
    HyperBlock class should be removed. The subclasses should extend Block class
    directly and the build function should build connected Keras layers instead of
    Blocks.

    # Arguments
        name: String. The name of the block. If unspecified, it will be set
        automatically with the class name.
    """

    def build(self, hp, inputs=None):
        """Build the HyperModel instead of Keras Model.

        # Arguments
            hp: Hyperparameters. The hyperparameters for building the model.
            inputs: A list of instances of Node.

        # Returns
            An Node instance, the output node of the output Block.
        """
        raise NotImplementedError


class ImageBlock(HyperBlock):
    """HyperBlock for image data.

    The image blocks is a block choosing from ResNetBlock, XceptionBlock, ConvBlock,
    which is controlled by a hyperparameter, 'block_type'.

    # Arguments
        block_type: String. 'resnet', 'xception', 'vanilla'. The type of HyperBlock
            to use. If unspecified, it will be tuned automatically.
        normalize: Boolean. Whether to channel-wise normalize the images.
            If unspecified, it will be tuned automatically.
        augment: Boolean. Whether to do image augmentation. If unspecified,
            it will be tuned automatically.
    """

    def __init__(self,
                 block_type=None,
                 normalize=True,
                 augment=True,
                 seed=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.block_type = block_type
        self.normalize = normalize
        self.augment = augment
        self.seed = seed

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = input_node

        block_type = self.block_type or hp.Choice('block_type',
                                                  ['resnet', 'xception', 'vanilla'],
                                                  default='resnet')

        normalize = self.normalize
        if normalize is None:
            normalize = hp.Choice('normalize', [True, False], default=True)
        augment = self.augment
        if augment is None:
            augment = hp.Choice('augment', [True, False], default=True)
        if normalize:
            output_node = preprocessor.Normalization()(output_node)
        if augment:
            output_node = preprocessor.ImageAugmentation(seed=self.seed)(output_node)
        sub_block_name = self.name + '_' + block_type
        if block_type == 'resnet':
            output_node = block.ResNetBlock(name=sub_block_name)(output_node)
        elif block_type == 'xception':
            output_node = block.XceptionBlock(name=sub_block_name)(output_node)
        elif block_type == 'vanilla':
            output_node = block.ConvBlock(name=sub_block_name).build(output_node)
        return output_node


class TextBlock(HyperBlock):

    def __init__(self, vectorizer=None, pretraining=None, **kwargs):
        super().__init__(**kwargs)
        self.vectorizer = vectorizer
        self.pretraining = pretraining

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = input_node
        vectorizer = self.vectorizer or hp.Choice('vectorizer',
                                                  ['sequence', 'ngram'],
                                                  default='sequence')
        if not isinstance(input_node, node.TextNode):
            raise ValueError('The input_node should be a TextNode.')
        if vectorizer == 'ngram':
            output_node = preprocessor.TextToNgramVector()(output_node)
            output_node = block.DenseBlock()(output_node)
        else:
            output_node = preprocessor.TextToIntSequence()(output_node)
            output_node = block.EmbeddingBlock(
                pretraining=self.pretraining)(output_node)
            output_node = block.ConvBlock(separable=True)(output_node)
        return output_node


<<<<<<< HEAD
=======
class StructuredDataBlock(HyperBlock):

    def __init__(self,
                 column_types,
                 task=None,
                 feature_engineering=True,
                 # include_head=True,
                 **kwargs):
        super().__init__()
        self.feature_engineering = feature_engineering
        self.column_types = column_types
        self.task = task
        # self.include_head = include_head

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = input_node
        feature_engineering = self.feature_engineering
        if feature_engineering is None:
            feature_engineering = hp.Choice('feature_engineering',
                                            [True, False],
                                            default=True)
        if feature_engineering:
            output_node = preprocessor.FeatureEngineering(
                column_types=self.column_types)(output_node)
        if self.task == 'classification':
            lgbm_classifier = LightGBMClassifierBlock()
            output_node = lgbm_classifier.build(hp=hp, inputs=output_node)
        else:
            lgbm_regressor = LightGBMRegressorBlock()
            output_node = lgbm_regressor.build(hp=hp, inputs=output_node)
        return output_node


>>>>>>> ad31842f11bf2d51f2974cf6cc0afa22ee2365dc
class LightGBMClassifierBlock(HyperBlock):
    """Structured data classification with LightGBM.

    It can be used with preprocessors, but not other blocks or heads.

    # Arguments
        metrics: String. The type of the model's metrics. If unspecified,
            it will be 'accuracy' for classification task.
    """

    def __init__(self, metrics=None, **kwargs):
        super().__init__(**kwargs)
        self.metrics = metrics
        if self.metrics is None:
            self.metrics = ['accuracy']

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = input_node
        output_node = preprocessor.LightGBMClassifier()(output_node)
        output_node = block.IdentityBlock()(output_node)
        output_node = head_module.EmptyHead(loss='categorical_crossentropy',
                                            metrics=self.metrics)(output_node)
        return output_node


class LightGBMRegressorBlock(HyperBlock):
    """Structured data regression with LightGBM.

    It can be used with preprocessors, but not other blocks or heads.

    # Arguments
        metrics: String. The type of the model's metrics. If unspecified,
            it will be 'mean_squared_error' for regression task.
    """

    def __init__(self, metrics=None, **kwargs):
        super().__init__(**kwargs)
        self.metrics = metrics
        if self.metrics is None:
            self.metrics = ['mean_squared_error']

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = input_node
        output_node = preprocessor.LightGBMRegressor()(output_node)
        output_node = block.IdentityBlock()(output_node)
        output_node = head_module.EmptyHead(loss='mean_squared_error',
                                            metrics=self.metrics)(output_node)
        return output_node


class SupervisedStructuredDataPipelineBlock(HyperBlock):

    def __init__(self,
                 column_types,
                 feature_engineering=True,
                 module_type=None,
                 head=None,
                 lightgbm_block=None,
                 **kwargs):
        super().__init__()
        self.column_types = column_types
        self.feature_engineering = feature_engineering
        self.module_type = module_type
        self.head = head
        self.lightgbm_block = lightgbm_block

    def build_feature_engineering(self, hp, input_node):
        output_node = input_node
        feature_engineering = self.feature_engineering
        if feature_engineering is None:
            feature_engineering = hp.Choice('feature_engineering',
                                            [True, False],
                                            default=True)
        if feature_engineering:
            output_node = preprocessor.FeatureEngineering(
                column_types=self.column_types)(output_node)
        return output_node

    def build_body(self, hp, input_node):
        module_type = self.module_type or hp.Choice('module_type',
                                                    ['dense', 'lightgbm'],
                                                    default='lightgbm')
        if module_type == 'dense':
            output_node = block.DenseBlock()(input_node)
            output_node = self.head(output_node)
        elif module_type == 'lightgbm':
            output_node = self.lightgbm_block.build(hp, input_node)
        else:
            raise ValueError('Unsupported module'
                             'type: {module_type}'.format(
                                 module_type=module_type))
        return output_node

    def build(self, hp, inputs=None):
        input_node = nest.flatten(inputs)[0]
        output_node = self.build_feature_engineering(hp, input_node)
        return self.build_body(hp, output_node)


class StructuredDataBlock(SupervisedStructuredDataPipelineBlock):

    def __init__(self,
                 column_types,
                 feature_engineering=True,
                 name=None,
                 **kwargs):
        super().__init__(column_types=column_types,
                         feature_engineering=feature_engineering,
                         **kwargs)

    def build_body(self, hp, input_node):
        return block.DenseBlock()(input_node)


class StructuredDataClassifierBlock(StructuredDataBlock):

    def __init__(self,
                 column_types,
                 feature_engineering=True,
                 module_type=None,
                 loss=None,
                 metrics=None,
                 **kwargs):
        self.loss = loss
        self.metrics = metrics
        super().__init__(
            column_types=column_types,
            feature_engineering=feature_engineering,
            module_type=module_type,
            head=head_module.ClassificationHead(loss=self.loss,
                                                metrics=self.metrics),
            lightgbm_block=LightGBMClassifierBlock(metrics=self.metrics))


class StructuredDataRegressorBlock(StructuredDataBlock):

    def __init__(self,
                 column_types,
                 feature_engineering=True,
                 module_type=None,
                 loss=None,
                 metrics=None,
                 **kwargs):
        self.loss = loss
        self.metrics = metrics
        super().__init__(
            column_types=column_types,
            feature_engineering=feature_engineering,
            module_type=module_type,
            head=head_module.RegressionHead(loss=self.loss,
                                            metrics=self.metrics),
            lightgbm_block=LightGBMRegressorBlock(metrics=self.metrics))


class TimeSeriesBlock(HyperBlock):

    def build(self, hp, inputs=None):
        raise NotImplementedError


class GeneralBlock(HyperBlock):
    """A general neural network block when the input type is unknown. """

    def build(self, hp, inputs=None):
        raise NotImplementedError
