"""Module for handling all the global variables for llvm workflow."""
import logging
from typing import Dict, Optional

import llvm

from arx.codegen.jit import ArxJIT
from arx.parser import Parser

IS_BUILD_LIB: bool = False


class ArxLLVM:
    """ArxLLVM gathers all the main global variables for LLVM workflow."""

    context: Optional[llvm.LLVMContext] = None
    module: Optional[llvm.Module] = None

    ir_builder: Optional[llvm.IRBuilder] = None
    di_builder: Optional[llvm.DIBuilder] = None

    jit: Optional[ArxJIT] = None

    named_values: Dict[str, llvm.AllocaInst] = {}
    function_protos: Dict[str, Parser.PrototypeAST] = {}
    exit_on_err: llvm.ExitOnError = llvm.ExitOnError()

    FLOAT_TYPE: Optional[llvm.Type] = None
    DOUBLE_TYPE: Optional[llvm.Type] = None
    INT8_TYPE: Optional[llvm.Type] = None
    INT32_TYPE: Optional[llvm.Type] = None
    VOID_TYPE: Optional[llvm.Type] = None

    DI_FLOAT_TYPE: Optional[llvm.DIType] = None
    DI_DOUBLE_TYPE: Optional[llvm.DIType] = None
    DI_INT8_TYPE: Optional[llvm.DIType] = None
    DI_INT32_TYPE: Optional[llvm.DIType] = None
    DI_VOID_TYPE: Optional[llvm.DIType] = None

    @staticmethod
    def get_data_type(type_name: str) -> Optional[llvm.Type]:
        """
        Get the LLVM data type for the given type name.

        Parameters
        ----------
            type_name (str): The name of the type.

        Returns
        -------
            Optional[llvm.Type]: The LLVM data type.
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
    def get_di_data_type(di_type_name: str) -> Optional[llvm.DIType]:
        """
        Get the LLVM debug information data type for the given type name.

        Parameters
        ----------
            di_type_name (str): The name of the type.

        Returns
        -------
            Optional[llvm.DIType]: The LLVM debug information data type.
        """
        if di_type_name == "float":
            return ArxLLVM.DI_FLOAT_TYPE
        elif di_type_name == "double":
            return ArxLLVM.DI_DOUBLE_TYPE
        elif di_type_name == "int8":
            return ArxLLVM.DI_INT8_TYPE
        elif di_type_name == "int32":
            return ArxLLVM.DI_INT32_TYPE
        elif di_type_name == "char":
            return ArxLLVM.DI_INT8_TYPE
        elif di_type_name == "void":
            return ArxLLVM.DI_VOID_TYPE

        logging.error("[EE] di_type_name not valid.")
        return None

    @staticmethod
    def initialize() -> None:
        """Initialize ArxLLVM."""
        # initialize the target registry etc.
        llvm.InitializeAllTargetInfos()
        llvm.InitializeAllTargets()
        llvm.InitializeAllTargetMCs()
        llvm.InitializeAllAsmParsers()
        llvm.InitializeAllAsmPrinters()

        llvm.InitializeNativeTarget()
        llvm.InitializeNativeTargetAsmPrinter()
        llvm.InitializeNativeTargetAsmParser()

        ArxLLVM.context = llvm.LLVMContext()
        ArxLLVM.module = llvm.Module("arx jit", ArxLLVM.context)

        # Create a new builder for the module.
        ArxLLVM.ir_builder = llvm.IRBuilder(ArxLLVM.context)

        # Data Types
        ArxLLVM.FLOAT_TYPE = llvm.Type.getFloatTy(ArxLLVM.context)
        ArxLLVM.DOUBLE_TYPE = llvm.Type.getDoubleTy(ArxLLVM.context)
        ArxLLVM.INT8_TYPE = llvm.Type.getInt8Ty(ArxLLVM.context)
        ArxLLVM.INT32_TYPE = llvm.Type.getInt32Ty(ArxLLVM.context)
        ArxLLVM.VOID_TYPE = llvm.Type.getVoidTy(ArxLLVM.context)

        logging.info("initialize Target")

        # LLVM IR
        ArxLLVM.jit = ArxLLVM.exit_on_err(llvm.orc.ArxJIT.Create())
        ArxLLVM.module.setDataLayout(ArxLLVM.jit.get_data_layout())

        # Create a new builder for the module.
        ArxLLVM.di_builder = llvm.DIBuilder(ArxLLVM.module)

        # di data types
        ArxLLVM.DI_FLOAT_TYPE = ArxLLVM.di_builder.createBasicType(
            "float", 32, llvm.dwarf.DW_ATE_float
        )
        ArxLLVM.DI_DOUBLE_TYPE = ArxLLVM.di_builder.createBasicType(
            "double", 64, llvm.dwarf.DW_ATE_float
        )
        ArxLLVM.DI_INT8_TYPE = ArxLLVM.di_builder.createBasicType(
            "int8", 8, llvm.dwarf.DW_ATE_signed
        )
        ArxLLVM.DI_INT32_TYPE = ArxLLVM.di_builder.createBasicType(
            "int32", 32, llvm.dwarf.DW_ATE_signed
        )
