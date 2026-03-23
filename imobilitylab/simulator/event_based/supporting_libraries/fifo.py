
class FifoItem(object):

    def __init__(self, item):
        self.obj = item
        self.next_item = None
        self.previous_item = None

    def destroy(self):
        self.obj = None
        self.next_item = None
        self.previous_item = None
        del self


class FIFO(object):
    # Init statement: Object contains a Start, End and a length of the Object.
    def __init__(self):
        self.start = None
        self.end = None
        self.length = 0

    def add_item(self, item: FifoItem):
        """Function to add a tapin to the end of TapinFIFO
        NOTE: Expects the input data is sorted. There is no ordering in the Class itself."""
        if self.start is None:
            self.start = item
            self.end = item
        else:
            self.end.next_item = item
            item.previous_item = self.end
            self.end = item
        self.length += 1
        #if self.type == 'PAS':
        #    print('() () ADD',self.start,self.length)

    def remove_item(self, item: FifoItem):
        if item.previous_item is not None:
            item.previous_item.next_item = item.next_item
            if item.next_item is not None:
                item.next_item.previous_item = item.previous_item
            else:
                self.end = item.previous_item
        else:
            self.start = item.next_item
            if item.next_item is not None:
                item.next_item.previous_item = item.previous_item
            else:
                self.end = item.previous_item
        item.destroy()
        self.length -= 1
        #if self.type == 'PAS':
        #    print('() () remove',self.start,self.length)

    def get_item(self):
        """Function to return the tapin of the self element.
        Returns none if there is no start set, else returns self.Start"""
        pom = self.start
        if pom is None:
            return None
        #if self.type == 'PAS':
        #    print('()() NEXT ITEM ',self.start.next_item, self.length)
        self.start = self.start.next_item
        self.length -= 1
        if self.start is None:
            self.end = None
        else:
            self.start.previous_item = None
        obj = pom.obj
        pom.destroy()
        #if self.type == 'PAS':
        #    print('()() GET ', self.start, self.length)
        return obj

    def destroy(self):
        """Function to delete the object"""
        if self.start is not None:
            item = self.start
            while item is not None:
                item.destroy()
                item = item.next_item
            self.start = None
            self.end = None
        del self