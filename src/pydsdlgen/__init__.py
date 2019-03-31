#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright (C) 2018-2019  UAVCAN Development Team  <uavcan.org>
# This software is distributed under the terms of the MIT License.
#
"""Code generator built on top of pydsdl.

Pydsdlgen uses pydsdl to generate test files using templates. While these
text files are often source code this module can also be used to generate
documentation or data interchange formats like JSON or XML.

"""

from typing import List, Dict, Iterable

import sys

from pathlib import Path, PurePath
from pydsdl.data_type import CompoundType
from pydsdl import parse_namespace

if sys.version_info[:2] < (3, 5):   # pragma: no cover
    print('A newer version of Python is required', file=sys.stderr)
    sys.exit(1)

# +---------------------------------------------------------------------------+


def _build_paths(paths: Iterable[str], resolve_paths: bool, required: bool) -> List[str]:
    """Helper method to build pathlib objects.

    Creates pathlib objects from input strings and handles various path flags.

    :param iterable paths: A list of path-like strings.
    :param bool resolve_paths: If True then each Path object will be resolved. For most
        platforms this yields absolute paths.
    :param bool required: If True and if the Path constructed ends up pointing to a
        non-existent file or folder then FileNotFoundError will be raised.

    :returns: A list of paths.

    :raises FileNotFoundError: If required is True and a path to a non-existent resource
                               is found.
    """
    result = []
    for path_string in paths:
        path = Path(path_string)
        if resolve_paths:
            path = path.resolve()

        if required and not path.exists:
            raise FileNotFoundError("{} did not exist.".format(path_string))

        result.append(str(path))

    return result


def parse_all(root_namespaces: Iterable[str], extra_includes: Iterable[str]) -> List[CompoundType]:
    """Parses all root namespaces.

    Locates the specified input files and collects all pydsdl parsed types into a single list.

    :param iterable root_namespaces: A list of paths to root namespaces for dsdl to parse.
    :param iterable extra_includes: Other dsdl namespaces that contain dependent types.

    :returns: A list of pydsdl types.

    :raises FileNotFoundError: If any of the root namespace folders were not found.
    :raises RuntimeError: If parsing a given root namespace yielded no types.
    """
    root_namespace_paths = _build_paths(root_namespaces, True, True)

    extra_include_paths = _build_paths(extra_includes, True, False)

    types = list()  # type: ignore

    for root_namespace_path in root_namespace_paths:
        types += parse_namespace(root_namespace_path, extra_include_paths)
        if len(types) == 0:
            raise RuntimeError(
                "Root namespace {} yielded no types.".format(root_namespace_path))

    return types


def generate_target_paths(types: List[CompoundType],
                          output_dir: str, extension:
                          str, resolve_paths: bool = True) -> Dict[CompoundType, Path]:
    """Generates a map of types to generated files.

    Given a list of pydsdl types, this method returns a map of type to the
    file that will be generated by a generator. By pre-determining the output
    file this library allows build systems to properly build dependencies before
    running the generation step.

    :param list types: A list of pydsdl types.
    :param str output_dir: The base directory under which all generated files will be created.
    :param str extension: The extension to use for generated file types. All paths and filenames
            are built using pathlib. See pathlib documentation for platform differences
            when forming paths, filenames, and extensions.
    :param bool resolve_path: If true then all paths will be resolved using pathlib.

    :returns: A map of pydsdl type to the path the type will be generated at.

    """
    base_path = PurePath(output_dir)

    type_to_output_map = dict()

    for dsdl_type in types:
        '''
        For each type we form a path with the output_dir as the base; the intermediate
        folders named for the type's namespaces; and a file name that includes the type's
        short name, major version, minor version, and the extension argument as a suffix.
        Python's pathlib adapts the provided folder and file names to the platform
        this script is running on.
        '''
        namespace_components = dsdl_type.full_namespace.split('.')
        filestem = "{}_{}_{}".format(
            dsdl_type.short_name, dsdl_type.version.major, dsdl_type.version.minor)
        output_path = Path(
            base_path / PurePath(*namespace_components) / PurePath(filestem).with_suffix(extension))
        if resolve_paths:
            output_path = output_path.resolve()
        type_to_output_map[dsdl_type] = output_path

    return type_to_output_map
