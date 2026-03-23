class ListItem():

    def __init__(self, _obj, _weight, _att2, _previous=None, _next=None):
        self.previous =_previous
        self.weight =_weight
        self.att2 =_att2
        self.obj =_obj
        self.next =_next

    def destroy(self):
        self.previous = None
        self.next = None
        self.obj = None
        del self


class PriorityFront():

    def __init__(self, ascending=False):
        self.start = None
        self.num = 0
        self.end = None
        self.half = None
        self.ascending = ascending

    def __search_for_placement__(self, item:ListItem, weight):

        if self.ascending:
            while item is not None:
                if weight < item.weight:
                    return item
                item = item.next
        else:
            while item is not None:
                if weight > item.weight:
                    return item
                item = item.next
        return None

    def AddItem(self, obj, weight, att2=None, newItem: ListItem = None):
        #print('@@@@@@@@@@@ ADDD ')
        if newItem is None:
            newItem = ListItem(obj, weight, att2)
        #print('@@@@@@@@@@@ ADDD ')
        #newItem = ListItem(obj, weight, att2)
        if self.start is None:
            #print('NEW START #',weight,'##########')
            self.start = newItem
            self.end = newItem
        else:
            umiest = False
            if self.ascending:
                #print('#####',self.start.weight,weight,'##########')
                if self.start.weight > weight:
                    self.start.previous = newItem
                    newItem.next = self.start
                    self.start = newItem
                elif self.end.weight <= weight:
                    self.end.next = newItem
                    newItem.previous = self.end
                    self.end = newItem
                else:
                    #if self.half is not None:
                    #    if self.half.weight > weight:
                    #        item = self.start.next
                    #    else:
                    #        item = self.half
                    #else:
                    #    item = self.start.next
                    #i = 1
                    insert_to = self.__search_for_placement__(self.start.next,weight)
                    #while item is not None:
                    #    if weight < item.weight:
                    #        umiest = True
                    #        break
                    #    #if 2 == int(self.num/i):
                    #    #    self.half = item
                    #   # i += 1
                    #    item = item.next
                    if insert_to is not None:
                        pom = insert_to.previous
                        insert_to.previous = newItem
                        newItem.next = insert_to
                        newItem.previous = pom
                        pom.next = newItem
                    else:
                        self.end.next = newItem
                        newItem.previous = self.end
                        self.end = newItem
                    if newItem.next is None:
                        self.end = newItem
            else:
                if self.start.weight<weight:
                    self.start.previous=newItem
                    newItem.next=self.start
                    self.start=newItem
                elif self.end.weight>weight:
                    self.end.next=newItem
                    newItem.previous=self.end
                    self.end=newItem
                else:
                    #if self.half is not None:
                    #    if self.half.weight<weight:
                    #        item=self.start.next
                    #    else:
                    #        item=self.half
                    #else:
                    #    item=self.start.next
                    #i=1
                    insert_to = self.__search_for_placement__(self.start, weight)
                    #item = self.start
                    #while item is not None:
                    #    if weight>item.weight:
                    #        pom=item.previous
                    #        item.previous=newItem
                    #        newItem.next=item
                    #        newItem.previous=pom
                    #        pom.next=newItem
                    #        umiest=True
                    #        break
                        #if 2==int(self.num/i):
                        #    self.half=item
                        #i+=1
                    #    item=item.next

                    if insert_to is not None:
                        pom = insert_to.previous
                        insert_to.previous = newItem
                        newItem.next = insert_to
                        newItem.previous = pom
                        pom.next = newItem
                    else:
                        self.end.next=newItem
                        newItem.previous=self.end
                        self.end = newItem
                    if newItem.next is None:
                        self.end=newItem
        self.num += 1


    def AddItem_with_return(self, obj, weight, att2=None):
        newItem = ListItem(obj, weight, att2)
        self.AddItem(obj, weight, att2, newItem)
        return newItem


    def AddItem_from_the_specific_location_with_return(self, insert_after_item:ListItem, obj, weight, att2=None):
        newItem = ListItem(obj, weight, att2)

        if self.ascending:
            if self.start.weight > weight:
                self.start.previous = newItem
                newItem.next = self.start
                self.start = newItem
            elif self.end.weight <= weight:
                self.end.next = newItem
                newItem.previous = self.end
                self.end = newItem
            else:
                insert_to = self.__search_for_placement__(insert_after_item, weight)
                if insert_to is not None:
                    pom = insert_to.previous
                    insert_to.previous = newItem
                    newItem.next = insert_to
                    newItem.previous = pom
                    pom.next = newItem
                else:
                    self.end.next = newItem
                    newItem.previous = self.end
                    self.end = newItem
                if newItem.next is None:
                    self.end = newItem
        else:
            if self.start.weight < weight:
                self.start.previous = newItem
                newItem.next = self.start
                self.start = newItem
            elif self.end.weight > weight:
                self.end.next = newItem
                newItem.previous = self.end
                self.end = newItem
            else:
                insert_to = self.__search_for_placement__(insert_after_item, weight)
                if insert_to is not None:
                    pom = insert_to.previous
                    insert_to.previous = newItem
                    newItem.next = insert_to
                    newItem.previous = pom
                    pom.next = newItem
                else:
                    self.end.next = newItem
                    newItem.previous = self.end
                    self.end = newItem
                if newItem.next is None:
                    self.end = newItem
        self.num += 1
        return newItem


    def InsertItem_After_the_specific_location_with_return(self, insert_after_item:ListItem, obj, weight, att2=None):
        newItem = ListItem(obj, weight, att2)
        if self.end == insert_after_item:
            newItem.previous = insert_after_item
            insert_after_item.next = newItem
            self.end = newItem
        else:
            newItem.previous = insert_after_item
            newItem.next = insert_after_item.next
            insert_after_item.next.previous = newItem
            insert_after_item.next = newItem
        self.num += 1
        return newItem


    def InsertItem_Before_the_specific_location_with_return(self, insert_before_item:ListItem, obj, weight, att2=None):
        newItem = ListItem(obj, weight, att2)
        if self.start == insert_before_item:
            newItem.next = insert_before_item
            insert_before_item.previous = newItem
            self.start = newItem
        else:
            newItem.next = insert_before_item
            newItem.previous = insert_before_item.previous
            insert_before_item.previous.next = newItem
            insert_before_item.previous = newItem

        self.num += 1
        return newItem

    def RemoveItem(self):
        if self.start is not None:
            item = (self.start.obj, self.start.weight, self.start.att2)
            pomT = self.start
            self.start = self.start.next
            pomT.destroy()
            self.num -= 1
            if self.num == 0:
                self.end = None
            return item
        else:
            return None

    def RemoveExactItem(self, obj, weight):
        if self.ascending:
            if self.half!=None:
                if self.half.weight>weight:
                    item=self.half
                    while(item!=None):
                        if obj==item.obj:
                            if item.next!=None and item.previous!=None:
                                #item.next=item.next.next
                                item.next.previous=item.previous
                                item.previous.next=item.next
                            if item==self.end:
                                self.end=item.previous
                                if item.previous!=None:
                                    item.previous.next=None
                            if item==self.start:
                                self.start=item.next
                                if item.next !=None:
                                    item.next.previous=None
                            if item==self.half:
                                self.half=None
                            return True
                        item=item.next
                else:
                    item=self.start
                    while(item!=None):
                        if obj==item.obj:
                            if item.next!=None and item.previous!=None:
                                #item.next=item.next.next
                                item.next.previous=item.previous
                                item.previous.next=item.next
                            if item==self.end:
                                self.end=item.previous
                                if item.previous!=None:
                                    item.previous.next=None
                            if item==self.start:
                                self.start=item.next
                                if item.next !=None:
                                    item.next.previous=None
                            if item==self.half:
                                self.half=None
                            return True
                        item=item.next
            else:
                item=self.start
                while(item!=None):
                    if obj==item.obj:
                        if item.next!=None and item.previous!=None:
                            #item.next=item.next.next
                            item.next.previous=item.previous
                            item.previous.next=item.next
                        if item==self.end:
                            self.end=item.previous
                            if item.previous!=None:
                                item.previous.next=None
                        if item==self.start:
                            self.start=item.next
                            if item.next !=None:
                                item.next.previous=None
                        if item==self.half:
                            self.half=None
                        return True
                    item=item.next
        else:
            if self.half!=None:
                if self.half.weight<weight:
                    item=self.half
                    while(item!=None):
                        if obj==item.obj:
                            return True
                        item=item.next
                else:
                    item=self.start
                    while(item!=None):
                        if obj==item.obj:
                            if item.next!=None and item.previous!=None:
                                #item.next=item.next.next
                                item.next.previous=item.previous
                                item.previous.next=item.next
                            if item==self.end:
                                self.end=item.previous
                                if item.previous!=None:
                                    item.previous.next=None
                            if item==self.start:
                                self.start=item.next
                                if item.next !=None:
                                    item.next.previous=None
                            if item==self.half:
                                self.half=None
                            return True
                        item=item.next
            else:
                item=self.start
                while(item!=None):
                    if obj==item.obj:
                        if item.next!=None and item.previous!=None:
                            #item.next=item.next.next
                            item.next.previous=item.previous
                            item.previous.next=item.next
                        if item==self.end:
                            self.end=item.previous
                            if item.previous!=None:
                                item.previous.next=None
                        if item==self.start:
                            self.start=item.next
                            if item.next !=None:
                                item.next.previous=None
                        if item==self.half:
                            self.half=None
                        return True
                    item=item.next
        return False

