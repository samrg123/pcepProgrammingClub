import argparse
import random

from src.sortingAlgorithms import *
from src.sortingAnimations import Sorter, SorterData


class MySelectionSort(Sorter):
    def implementation(self, data:SorterData) -> None:
        
        # TODO: Implement your own selection sort algorithm here
        
        pass


def main(mainArgs:list[str]|None = None) -> None:

    # register sorter algorithms
    sorterAlgorithms = { x.__name__.lower():x for x in (MySelectionSort, BubbleSort, SelectionSort, QuickSort, InsertionSort, HeapSort, MergeSort) }

    # build program arguments
    argParser = argparse.ArgumentParser(
        prog        = "SortingAnimations",
        description = "A visualization algorithm for various sorting algorithms"
    )

    argParser.add_argument("algorithm"      , choices=sorterAlgorithms.keys())
    argParser.add_argument("--size"         , type=int   , default=20)
    argParser.add_argument("--frameTime"    , type=float , default=1/30)
    argParser.add_argument("--defaultDelay" , type=float , default=10e-3)
    argParser.add_argument("--readDelay"    , type=float)
    argParser.add_argument("--writeDelay"   , type=float)
    argParser.add_argument("--compareDelay" , type=float)
    argParser.add_argument("--checkDelay"   , type=float)
    argParser.add_argument("--barColor"     , type=str   , default="skyblue")
    argParser.add_argument("--readColor"    , type=str   , default="blue")
    argParser.add_argument("--writeColor"   , type=str   , default="maroon")
    argParser.add_argument("--compareColor" , type=str   , default="orange")

    args = argParser.parse_args(mainArgs)

    # generate a random list of numbers 
    shuffledValues = list(range(1, args.size + 1))
    random.shuffle(shuffledValues)
 
    # create the sorter and sort!
    # The call to sort will block execution even after completed until close the visualization window
    sorter = sorterAlgorithms[args.algorithm]()
 
    sorter.sort(
        values              = shuffledValues,
        defaultBarColor     = args.barColor,
        frameTime           = args.frameTime,
        registerCloseEvents = True,
        events              = SorterEvents(
            Read    = SorterEvent(color=args.readColor,    delaySec=args.defaultDelay if args.readDelay    is None else args.readDelay),
            Write   = SorterEvent(color=args.writeColor,   delaySec=args.defaultDelay if args.writeDelay   is None else args.writeDelay),
            Compare = SorterEvent(color=args.compareColor, delaySec=args.defaultDelay if args.compareDelay is None else args.compareDelay),
            Valid   = SorterEvent(color="green",           delaySec=args.defaultDelay if args.checkDelay   is None else args.checkDelay),
            Invalid = SorterEvent(color="red",             delaySec=args.defaultDelay if args.checkDelay   is None else args.checkDelay),
        )
    )

if __name__ == "__main__":
    main()