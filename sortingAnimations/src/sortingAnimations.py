import enum
import os
import signal
import time
from dataclasses import dataclass, field
from enum import IntEnum
from threading import RLock, Thread
from typing import Any, Callable, Generator

import matplotlib.pyplot as plt
from matplotlib import animation, container, patches, patheffects


@dataclass
class SorterEvent():
    color    :str
    delaySec :float = 2e-3
    count    :int   = 0
    enabled  :bool  = True 

@dataclass
class SorterEvents():
    Read    :SorterEvent = field(default_factory = lambda: SorterEvent("blue"))
    Write   :SorterEvent = field(default_factory = lambda: SorterEvent("orange"))
    Compare :SorterEvent = field(default_factory = lambda: SorterEvent("purple"))
    Valid   :SorterEvent = field(default_factory = lambda: SorterEvent("green"))
    Invalid :SorterEvent = field(default_factory = lambda: SorterEvent("red"))

class SorterState(IntEnum):
    Initializing  = enum.auto()
    Sorting       = enum.auto()
    Sorted        = enum.auto()
    Verifying     = enum.auto()
    Verified      = enum.auto()
    Complete      = enum.auto()

class Sorter():
    implementation :Callable[["Sorter"], "SorterData"]

    _state: SorterState

    _fig             :plt.Figure
    _ax              :plt.Axes
    _ani             :animation.FuncAnimation
    _bars            :container.BarContainer
    _dirtyBarIndices : set[int]
    _defaultBarColor = "black"  

    _data     :"SorterData"
    _contents :list[Any] 

    _sortStartNs:int
    _sortStopNs :int

    def _runImplementation(self) -> None:
        implementation = getattr(self, "implementation", None)
        if implementation is None:
            raise NotImplementedError(f"Missing implementation! Please extend Sorted class with implementation method")
        
        self._sortStartNs = time.time_ns()
        self._state = SorterState.Sorting

        implementation(self._data)

        self._sortStopNs = time.time_ns()
        self._state = SorterState.Sorted

    def _runVerification(self) -> None:
        sortedContent = sorted(self._contents)

        for i in range(len(sortedContent)):
            value = self._data[i]
            if value.content != sortedContent[i]:
                self._data.setEvent(self._data.events.Invalid, value)
            else:
                self._data.setEvent(self._data.events.Valid, value) 

        self._state = SorterState.Verified


    def _updateFigure(self, frame:int) -> None:
        if self._state == SorterState.Initializing or self._state == SorterState.Complete:
            return

        # cache data variables
        with self._data.lock:
            sortNs = (time.time_ns() - self._sortStartNs) if self._state == SorterState.Sorting else \
                     (self._sortStopNs - self._sortStartNs)

            readCount    = self._data.events.Read.count
            writeCount   = self._data.events.Write.count
            compareCount = self._data.events.Compare.count
            invalidCount = self._data.events.Invalid.count

            dataUpdates = self._data.getUpdates()

        # update title 
        self._ax = self._fig.gca()
        self._ax.set_title(f"Items: {len(self._data)}\nFrame: {frame} | Time: {(sortNs*1e-9):.2f} | Reads: {readCount} | Writes: {writeCount} | Compares: {compareCount}")

        # clean dirty colors on update
        if dataUpdates:
            for i in self._dirtyBarIndices:
                barRect:patches.Rectangle = self._bars[i]
                barRect.set_color(self._defaultBarColor)
            self._dirtyBarIndices.clear()

        # update bars
        for index,value,event in dataUpdates:
            barRect:patches.Rectangle = self._bars[index]
            barRect.set_height(value)
            barRect.set_color(event.color)

            # flag color to be reset on next update
            # Note: we intentionally leave old colors on the screen while verifying
            if self._state == SorterState.Sorting:
                self._dirtyBarIndices.add(index)

        # update state
        match self._state:

            case SorterState.Sorted:
                
                # disable events associated with sorting
                self._data.events.Read.enabled    = False
                self._data.events.Write.enabled   = False
                self._data.events.Compare.enabled = False
                
                # kick off verification on another thread
                self._state = SorterState.Verifying
                Thread(target=self._runVerification).start()

            case SorterState.Verified:
                self._state = SorterState.Complete

                # add pass/fail overlay
                if invalidCount == 0:
                    verificationString = "PASS"
                    verificationColor  = "green"
                else:
                    verificationString = f"FAIL {invalidCount} ERRORS"
                    verificationColor  = "red"

                text = self._ax.text(
                    x                   = len(self._bars)/2, 
                    y                   = .75*(max(self._bars.datavalues) - min(self._bars.datavalues)), 
                    s                   = verificationString, 
                    size                = 20, 
                    color               = verificationColor, 
                    weight              = "bold", 
                    horizontalalignment = "center", 
                    verticalalignment   = "center"
                )

                text.set_path_effects([patheffects.withStroke(linewidth=5, foreground="white")])


    def sort(self, values:list[Any], defaultBarColor:str = "skyblue", events:SorterEvents = None, frameTime:float = 1/30, registerCloseEvents:bool=False) -> list[Any]:

        # create data
        self._state = SorterState.Initializing
        if events is None:
            events = SorterEvents()
    
        # Note: we cache the original content so we can cross reference it during verification to make sure nothing is missing
        self._data = SorterData(values, events)
        self._contents = values.copy()

        # create figure
        self._fig  = plt.figure(type(self).__name__)
        self._ax   = self._fig.gca()

        dataLength = len(self._data)
        self._dirtyBarIndices = set()
        self._defaultBarColor = defaultBarColor
        self._bars = self._ax.bar(range(dataLength), self._data.getContents(), color=([defaultBarColor] * dataLength))
        
        # register close events
        if registerCloseEvents:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            self._fig.canvas.mpl_connect('close_event', lambda e: os._exit(0))


        # show the unsorted data
        plt.show(block=False)

        # start sorting on background thread
        thread = Thread(target = self._runImplementation)
        thread.start()
        

        # update the plot
        # Note: FuncAnimation lags when sorting thread doesn't sleep for long delaySeconds so 
        #       manually animate the graph here for smoother updates
        i = 0
        lastUpdateTime = time.time()
        while self._state != SorterState.Complete:
            self._updateFigure(i)
            
            updateTime = time.time()
            deltaT = updateTime - lastUpdateTime

            # Note: we need to give matplotlib some reasonable amount of time
            #       to process input, otherwise it will lock up so we always 
            #       pause for at least wait 1 microsecond 
            pauseTime = max(1e-6, frameTime - deltaT)
            plt.pause(pauseTime)

            lastUpdateTime = updateTime
            i+=1


        # block until main window is closed 
        plt.show(block=True)

        # return results 
        return self._data.getContents()
    

class SorterData():
    events :SorterEvents
    lock = RLock()

    _values         :list["SorterValue"]
    _valueIndexMap  :dict["SorterValue", set[int]]
    _updateIndexMap :dict[int, SorterEvent]

    def __init__(self, contents:list[Any], events:SorterEvents):
        self.events          = events
        self._values         = []
        self._updateIndexMap = {}
        self._valueIndexMap  = {}

        for i, content in enumerate(contents):
            value = SorterValue(self, content)
            self._values.append(value)
            self._valueIndexMap[value] = set([i])

    def __len__(self) -> int:
        return len(self._values)

    def _setEvent(self, event:SorterEvent, *indices:int) -> None:
        if not event.enabled:
            return

        event.count+= 1
        for i in indices: 
            self._updateIndexMap[i] = event

    def __getitem__(self, index:int) -> "SorterValue":
        with self.lock:
            value = self._values[index]
            self._setEvent(self.events.Read, index)

        time.sleep(self.events.Read.delaySec)
        return value

    def __iter__(self) -> Generator["SorterValue", None, None]:
        with self.lock:        
            iterator = self._values.__iter__()

        # Warn: This isn't super thread safe, but neither are native python iterators
        for i,x in enumerate(iterator):
            with self.lock:
                self._setEvent(self.events.Read, i)

            time.sleep(self.events.Read.delaySec)
            yield x

    def __setitem__(self, index:int, value:"SorterValue") -> None:
        with self.lock:
            oldValue = self._values[index]
            
            self._values[index] = value

            self._valueIndexMap[oldValue].remove(index)
            self._valueIndexMap[value].add(index)
            
            self._setEvent(self.events.Write, index)

        time.sleep(self.events.Write.delaySec)

    def setEvent(self, event:SorterEvent, *values:"SorterValue") -> None:
        with self.lock:
            indices:list[int] = []
            for value in values:
                indices+= self._valueIndexMap[value]

            self._setEvent(event, *indices)

        time.sleep(event.delaySec)        

    def getContents(self) -> list[Any]:
        with self.lock:        
            return [x.content for x in self._values]
        
    def getUpdates(self) -> list[tuple[int, Any, SorterEvent]]:
        with self.lock:
            result = [(index, self._values[index].content, event) for index,event in self._updateIndexMap.items()]
            self._updateIndexMap.clear()
        return result


@dataclass(frozen=True)
class SorterValue():
    data    :SorterData
    content :Any

    def __hash__(self) -> int:
        return super().__hash__()
    
    def __lt__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content < other.content
    
    def __le__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content <= other.content    
    
    def __gt__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content > other.content
    
    def __ge__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content >= other.content    

    def __eq__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content == other.content
    
    def __ne__(self, other:"SorterValue") -> bool:
        self.data.setEvent(self.data.events.Compare, self, other)
        return self.content != other.content    

    def __str__(self) -> str:
        return str(self.content)
