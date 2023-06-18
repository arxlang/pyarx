"""Module for handling all the global variables for llvm workflow."""
import logging
from typing import Dict, Optional, Any

import llvmlite.binding as llvm


IS_BUILD_LIB: bool = False

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


class ArxLLVM:
    """ArxLLVM gathers all the main global variables for LLVM workflow."""

    context: Optional[llvm.ir.context.Context] = None
    module: Optional[llvm.ir.module.Module] = None

    ir_builder: Optional[llvm.ir.builder.IRBuilder] = None

    named_values: Dict[str, Any] = {}  #  AllocaInst

    FLOAT_TYPE: Optional[llvm.ir.types.Type] = None
    DOUBLE_TYPE: Optional[llvm.ir.types.Type] = None
    INT8_TYPE: Optional[llvm.ir.types.Type] = None
    INT32_TYPE: Optional[llvm.ir.types.Type] = None
    VOID_TYPE: Optional[llvm.ir.types.Type] = None

    @staticmethod
    def get_data_type(type_name: str) -> Optional[llvm.ir.types.Type]:
        """
        Get the LLVM data type for the given type name.

        Parameters
        ----------
            type_name (str): The name of the type.

        Returns
        -------
            Optional[ir]: The LLVM data type.
        """
        if type_name == "float":
            return ArxLLVM.FLOAT_TYPE
        elif type_name == "double":
            return ArxLLVM.DOUBLE_TYPE
        elif type_name == "int8":
            return ArxLLVM.INT8_TYPE
        elif type_name == "int32":
            return ArxLLVM.INT32_TYPE
        elif type_name == "char":
            return ArxLLVM.INT8_TYPE
        elif type_name == "void":
            return ArxLLVM.VOID_TYPE

        logging.error("[EE] type_name not valid.")
        return None

    @staticmethod
    def initialize() -> None:
        """Initialize ArxLLVM."""
        # initialize the target registry etc.
        llvm.initialize()
        llvm.initialize_all_asmprinters()
        llvm.initialize_all_targets()
        llvm.initialize_native_target()
        llvm.initialize_native_asmparser()
        llvm.initialize_native_asmprinter()

        # ArxLLVM.context = llvm.ir.context.Context()
        ArxLLVM.module = llvm.ir.module.Module("Arx")

        # Create a new builder for the module.
        ArxLLVM.ir_builder = llvm.ir.IRBuilder()

        # Data Types
        ArxLLVM.FLOAT_TYPE = llvm.ir.FloatType()
        ArxLLVM.DOUBLE_TYPE = llvm.ir.DoubleType()

        ArxLLVM.INT8_TYPE = llvm.ir.IntType(8)
        ArxLLVM.INT32_TYPE = llvm.ir.IntType(32)
        ArxLLVM.VOID_TYPE = llvm.ir.VoidType()

        logging.info("initialize Target")

        # Create a new builder for debugging
        # ArxLLVM.di_builder = llvm.DIBuilder(ArxLLVM.module)
        # di data types
        # ArxLLVM.DI_FLOAT_TYPE = ArxLLVM.di_builder.createBasicType(
        #     "float", 32, llvm.dwarf.DW_ATE_float
        # )
        # ArxLLVM.DI_DOUBLE_TYPE = ArxLLVM.di_builder.createBasicType(
        #     "double", 64, llvm.dwarf.DW_ATE_float
        # )
        # ArxLLVM.DI_INT8_TYPE = ArxLLVM.di_builder.createBasicType(
        #     "int8", 8, llvm.dwarf.DW_ATE_signed
        # )
        # ArxLLVM.DI_INT32_TYPE = ArxLLVM.di_builder.createBasicType(
        #     "int32", 32, llvm.dwarf.DW_ATE_signed
        # )
