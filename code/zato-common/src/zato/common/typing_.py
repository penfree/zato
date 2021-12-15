# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# ################################################################################################################################
# ################################################################################################################################

# stdlib
from typing import           \
    Any as any_,             \
    Callable as callable_,   \
    cast as cast_,           \
    Dict as dict_,           \
    Generator as generator_, \
    NoReturn as noreturn,    \
    List as list_,           \
    Optional as optional,    \
    Text as str_,            \
    Tuple as tuple_,         \
    Type as type_,           \
    TypeVar as typevar_,     \
    Set as set_,             \
    Union as union_

# dacite
from dacite import from_dict

# typing-extensions
from typing_extensions import \
    TypeAlias as typealias_


# Be explicit about which import error we want to catch
try:
    import dataclasses # noqa: F401

# Python 3.6
except ImportError:
    from zato.common.ext.dataclasses import * # noqa: F401

# Python 3.6+
else:
    from dataclasses import * # noqa: F401

# ################################################################################################################################
# ################################################################################################################################

#
# TypedDict
#
try:
    from typing import TypedDict
    from typing import Protocol
except ImportError:
    from zato.common.ext.typing_extensions import TypedDict
    from zato.common.ext.typing_extensions import Protocol

# ################################################################################################################################
# ################################################################################################################################

# For flake8
from_dict = from_dict
optional  = optional
Protocol  = Protocol
TypedDict = TypedDict

# ################################################################################################################################
# ################################################################################################################################

def instance_from_dict(class_, data):
    # type: (object, dict) -> object
    instance = class_()
    for key, value in data.items():
        setattr(instance, key, value)
    return instance

# ################################################################################################################################
# ################################################################################################################################

anydict      = dict_[any_, any_]
anylist      = list_[any_]
anyset       = set_[any_]
anytuple     = tuple_[any_, ...]
boolnone     = optional[bool]
callable_    = callable_[..., any_]
callnone     = optional[callable_]
cast_        = cast_
commondict   = dict_[str, union_[int, str_, bool, float, anydict, anylist, None]]
dictlist     = list_[anydict]
floatnone    = optional[float]
generator_   = generator_
intanydict   = dict_[int, any_]
intdict      = dict_[int, int]
intdictdict  = dict_[int, anydict]
intlist      = list_[int]
intnone      = optional[int]
intset       = set_[int]
intsetdict   = dict_[int, anyset]
intstrdict   = dict_[int, str]
noreturn     = noreturn
set_         = set_
stranydict   = dict_[str, any_]
strdictdict  = dict_[str, anydict]
strint       = union_[str_, int]
strintbool   = union_[str_, int, bool]
strintdict   = dict_[str, int]
strintnone   = union_[optional[str_], optional[int]]
strlist      = list_[str]
strlistdict  = dict_[str, anylist]
strlistempty = list_[optional[str]]
strnone      = optional[str]
strset       = set_[str]
strsetdict   = dict_[str, anyset]
strstrdict   = dict_[str, str]
strtuple     = tuple_[str, ...]
tuple_       = tuple_
type_        = type_
typealias_   = typealias_
typevar_     = typevar_
union_       = union_
