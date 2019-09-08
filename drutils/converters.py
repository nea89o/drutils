from typing import Callable, Union, Any, TypeVar, Type

from discord.ext.commands import Converter, UserInputError
from discord.utils import maybe_coroutine

C = TypeVar('C', bound=Converter)


class AugmentedConverter(Converter):
    """
    Augment an existing converter by mapping its result or filtering based on its output.

    Mapping is applied before filtering.

    """

    async def convert(self, ctx, argument):
        converter = self.original_converter
        if issubclass(converter, Converter):
            converter = converter()
        if isinstance(converter, Converter):
            converter = converter.convert
        result = await converter(ctx, argument)
        if await maybe_coroutine(self.filter_function(result)):
            return result
        raise UserInputError()

    def __init__(self, original_converter: Union[C, Type[C], Callable], mapping_function: Callable[[Any], Any] = None,
                 filter_function: Callable[[Any], bool] = None, error_message: str = None):
        """

        :param original_converter: the converter augment. can be a function, converter or converter class. must be async
        :param mapping_function:   maps the result of the converter before any filtering takes place. optional
        :param filter_function:    filters the result. if this function returns a falsey value an `UserInputError` is
                                   risen and then caught by discord.ext.commands
        :param error_message:      the error message that is thrown. this can be accessed by a custom error handler
        """
        self.original_converter = original_converter
        self.mapping_function = mapping_function or (lambda x: x)
        self.filter_function = filter_function or (lambda _: True)
        self.error_message = error_message


def non_nullable(converter: Union[C, Type[C], Callable], error_message: str = None):
    """
    augments a converter to raise a UserInputError when None is returned. Useful for Greedy or Optional matchers.

    :param converter:     the converter to augment
    :param error_message: the error message to be associated with the UserInputError
    :return:              the augmented converter
    """
    return AugmentedConverter(converter, filter_function=lambda res: res is not None, error_message=error_message)
