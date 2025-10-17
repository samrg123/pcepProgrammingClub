from .sortingAnimations import *

class BubbleSort(Sorter):
    def implementation(self, data:SorterData) -> None:
        countMinusOne = len(data) - 1
        for i in range(countMinusOne):
            for j in range(countMinusOne-i):
                v1 = data[j]
                v2 = data[j+1]

                if(v1 > v2):
                    data[j] = v2
                    data[j+1] = v1 

# Sanjay's implementation of selection sort (Thanks Sanjay!)
class SelectionSort(Sorter):
    def implementation(self, arr:SorterData) -> None:
        n = len(arr)
        for i in range(n):

            nextSmallestNum, currentValue = arr[i], arr[i]
            smallestNumIdx = i

            for j in range(i+1,n):

                if nextSmallestNum > arr[j]:
                    nextSmallestNum = arr[j]
                    smallestNumIdx = j
            
            arr[smallestNumIdx] = currentValue
            arr[i] = nextSmallestNum

class QuickSort(Sorter):
    def implementation(self, data:SorterData) -> None:
        self.sortRange(data, 0, len(data)-1)

    def sortRange(self, data:SorterData, startIndex:int, endIndex:int) -> None:
        numElements = endIndex - startIndex + 1
        if numElements <= 1:
            # nothing to sort
            return

        # partition the data into two sides where everything on the left of pivotIndex
        # is less than or equal to data[pivotIndex] and everything on the right is greater
        # Note: We pivot at the endIndex to make life easy, but this has O(n^2) time when data is already sorted. 
        #       A better option would be to pivot at the midpoint / median / randomly but that adds complexity to the algorithm
        pivotValue = data[endIndex]
        
        # partition the range [startIndex, endIndex)
        # maintaining the invariant that all values to the left of lowerIndex are less than or equal to pivotValue
        lowerIndex = startIndex
        for i in range(startIndex, endIndex):
            iValue = data[i]

            if iValue <= pivotValue:
                # append iValue to end of range [startIndex, lowerIndex) 
                data[i] = data[lowerIndex]
                data[lowerIndex] = iValue
                lowerIndex+= 1
                
        # at this point the values in range [startIndex, lowerIndex) are less than or equal to pivot values
        # and the values in range [lowerIndex, endIndex) are greater than pivotValue.
        # The last thing we need to do is swap our pivot value into the position at lowerIndex 
        data[endIndex] = data[lowerIndex]
        data[lowerIndex] = pivotValue
        pivotIndex = lowerIndex

        # sort the left side of pivot
        self.sortRange(data, startIndex, pivotIndex-1)

        # sort the right side of pivot
        self.sortRange(data, pivotIndex+1, endIndex)


class InsertionSort(Sorter):
    def implementation(self, data:SorterData) -> None:

        # sort the array maintaining the invariant that the values in range [0, i] are in sorted order
        for i in range(1, len(data)):
            iValue = data[i]
        
            # reverse search for correct location for iValue 
            j = i-1
            while j >= 0:
                jValue = data[j]
                
                if jValue <= iValue:
                    # everything in range [0, j] is less than or equal to iValue
                    break

                # shift data over to make room for iValue 
                data[j+1] = data[j]
                j-= 1

            # insert iValue into correct position
            data[j+1] = iValue
            
# Heap sort adopting max heap implementation from heapq
class HeapSort(Sorter):
    def implementation(self, data:SorterData) -> None:

        # build a max heap from data in-place, in O(n) time.
        n = len(data)
        # Transform bottom-up. The largest indedata there's any point to looking at
        # is the largest with a child index in-range, so must have 2*i + 1 < n,
        # or i < (n-1)/2.  If n is even = 2*j, this is (2*j-1)/2 = j-1/2 so
        # j-1 is the largest, which is n//2 - 1.  If n is odd = 2*j+1, this is
        # (2*j+1-1)/2 = j so j-1 is the largest, and that's again n//2-1.
        for i in reversed(range(n//2)):
            self._siftup_max(data, i, n)

        # data[0] is the maximum value on the heap
        # keep popping max value off, placing it at the end of the array, and fixing up the heap to keep invariance
        # Total time = O(n log(n)) 
        for i in range(n):
            heapEndIndex = n-1 - i

            # swap max value in the heap for last value in heap
            maxValue           = data[0]
            data[0]            = data[heapEndIndex]
            data[heapEndIndex] = maxValue 
            
            # fixup heap with size reduced by 1 
            self._siftup_max(data, 0, heapEndIndex)

    # 'heap' is a heap at all indices >= startpos, except possibly for pos.  pos
    # is the index of a leaf with a possibly out-of-order value.  Restore the
    # heap invariant.
    def _siftdown_max(self, heap:SorterData, startpos:int, pos:int) -> None:
        'Maxheap variant of _siftdown'
        newitem = heap[pos]
        # Follow the path to the root, moving parents down until finding a place
        # newitem fits.
        while pos > startpos:
            parentpos = (pos - 1) >> 1
            parent = heap[parentpos]
            if parent < newitem:
                heap[pos] = parent
                pos = parentpos
                continue
            break
        heap[pos] = newitem

    def _siftup_max(self, heap:SorterData, pos:int, endpos:int) -> None:
        startpos = pos
        newitem = heap[pos]
        # Bubble up the larger child until hitting a leaf.
        childpos = 2*pos + 1    # leftmost child position
        while childpos < endpos:
            # Set childpos to index of larger child.
            rightpos = childpos + 1
            if rightpos < endpos and not heap[rightpos] < heap[childpos]:
                childpos = rightpos
            # Move the larger child up.
            heap[pos] = heap[childpos]
            pos = childpos
            childpos = 2*pos + 1
        # The leaf at pos is empty now.  Put newitem there, and bubble it up
        # to its final resting place (by sifting its parents down).
        heap[pos] = newitem
        self._siftdown_max(heap, startpos, pos)


class MergeSort(Sorter):
    def implementation(self, data:SorterData) -> None:
        self.sortRange(data, 0, len(data)-1)

    def sortRange(self, data:SorterData, startIndex:int, endIndex:int) -> None:
        if endIndex <= startIndex:
            # Nothing left to sort
            return

        # split the array at its midpoint
        splitIndex = (endIndex - startIndex) // 2 + startIndex

        # sort the left side
        self.sortRange(data, startIndex, splitIndex)
        
        # sort the right side
        self.sortRange(data, splitIndex + 1, endIndex)

        # merge the sorted arrays
        self.merge(data, startIndex, splitIndex, splitIndex+1, endIndex)

    def merge(self, data:Sorter, startIndex1:int, endIndex1:int, startIndex2:int, endIndex2:int) -> None:

        # merge arrays [startIndex1, endIndex1] and [startIndex2, endIndex2] in sorted order
        while startIndex1 <= endIndex1 and startIndex2 <= endIndex2:
            value1 = data[startIndex1]
            value2 = data[startIndex2]

            if value1 <= value2:
                # value1 is in the right place
                startIndex1+= 1

            else:
                # Shift over elements to make room for value2
                i = startIndex2
                while i > startIndex1:
                    data[i] = data[i - 1]
                    i-= 1

                # insert value2 before value1
                data[startIndex1] = value2

                # adjust array lengths
                endIndex1+= 1
                startIndex1+= 1
                startIndex2+= 1
