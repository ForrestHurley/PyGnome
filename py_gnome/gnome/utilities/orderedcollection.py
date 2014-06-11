#!/usr/bin/env python
import types


class OrderedCollection(object):
    '''
    Generalized Container for a set of objects of a particular type which
    preserves the order of insertion and supports replacement of not only
    an object in the list, but the key/id that references it. (a normal
    OrderedDict can't do this)
    - The order of insertion is preserved.
    - Objects are accessed by id, as if in a dictionary.
    - Objects can be replaced in order.  The objects will be referenced
      by a new id, and still be in the correct order.
    '''

    def __init__(self, elems=None, dtype=None):
        if elems and not isinstance(elems, list):
            raise TypeError('%s: needs a list of objects'
                            % self.__class__.__name__)
        if not elems:
            elems = []

        if not dtype and len(elems) == 0:
            raise TypeError('%s: specify a data type if list is empty'
                            % self.__class__.__name__)
        elif not dtype:
            self.dtype = type(elems[0])
        else:
            self.dtype = dtype

        if not all([isinstance(e, self.dtype) for e in elems]):
            raise TypeError('%s: needs a list of %s'
                            % (self.__class__.__name__, self.dtype))

        # a bunch of Gnome classes have an id property defined, which we will
        # prefer
        # otherwise, we just take the id(e) value
        # NOTE: we stringify the e.id value since it could be of a type that
        # is hard to reference as a key

        self._index = dict([((str(e.id) if hasattr(e, 'id') else id(e)), idx)
                            for (idx, e) in enumerate(elems)])
        self._elems = elems[:]
        self.callbacks = {}

    def get(self, ident):
        return self._elems[self._index[ident]]

    def add(self, elem):
        'Add an object to the collection '

        if isinstance(elem, self.dtype):
            if hasattr(elem, 'id'):

                # A bunch of Gnome classes have an id property defined,
                # which we will prefer.
                # NOTE: the e.id value is stringified since the key has been
                # as well.
                l__id = str(elem.id)
            else:
                l__id = id(elem)

            if l__id not in self._index.keys():
                self._index[l__id] = len(self._elems)
                self._elems.append(elem)

                # fire add event only if elem is not already in the list
                self.fire_event('add', elem)
        elif isinstance(elem, list) and all([isinstance(e, self.dtype)
                for e in elem]):

            for e in elem:
                # this will call self.fire_event when the object is added to OC
                self.add(e)
        else:
            raise TypeError('{0}: expected {1}, '
                            'got {2}'.format(self.__class__.__name__,
                                             self.dtype,
                                             type(elem)))

    def remove(self, ident):
        ''' Remove an object from the collection '''

        # fire remove event before removing from collection
        self.fire_event('remove', self[ident])

        if ident in self._index:
            self._elems[self._index[ident]] = None
            del self._index[ident]
        else:
            self._elems[self._index[str(ident)]] = None
            del self._index[str(ident)]

    def replace(self, ident, new_elem):
        if not isinstance(new_elem, self.dtype):
            raise TypeError('{0}: expected {1}, '
                            'got {2}'.format(self.__class__.__name__,
                                             self.dtype,
                                             type(new_elem)))

        if ident in self._index.keys():
            l__key = ident
        elif str(ident) in self._index.keys():
            l__key = str(ident)
        else:
            self.add(new_elem)
            return

        # we have an existing object
        idx = self._index[l__key]
        del self._index[l__key]

        if hasattr(new_elem, 'id'):
            # a bunch of Gnome classes have an id property defined,
            # which we will prefer
            # NOTE: the e.id value is stringified since the key has been
            # as well.
            self._index[str(new_elem.id)] = idx
        else:
            self._index[id(new_elem)] = idx

        self._elems[idx] = new_elem
        self.fire_event('replace', new_elem)  # returns the newly added object

    def index(self, ident, renumber=True):
        idx = self._index[ident]
        if renumber:
            return sorted(self._index.values()).index(idx)
        else:
            return idx

    def get_by_index(self, index):
        'return object at specified index or ordered collection'
        ix = sorted(self._index.values())[index]
        return self._elems[ix]

    def __len__(self):
        return len(self._index.keys())

    def __iter__(self):
        for i in sorted(self._index.values()):
            yield self._elems[i]

    def __contains__(self, ident):
        try:
            return ident.id in self._index
        except AttributeError:
            return id(ident) in self._index

    def __getitem__(self, ident):
        return self.get(ident)

    def __setitem__(self, ident, new_elem):
        self.replace(ident, new_elem)

    def __delitem__(self, ident):
        self.remove(ident)

    def __iadd__(self, rop):
        self.add(rop)
        return self

    def __str__(self):
        # order by position in list
        itemlist = sorted(self._index.items(), key=lambda x: x[1])

        # reference the value in list
        itemlist = [(k, self._elems[v]) for (k, v) in itemlist]

        if len(itemlist) > 6:  # should we abbreviate the list?
            strlist = ['\t%s: %s,' % i for i in itemlist[:2]]
            strlist += ('\t...', '\t...')
            strlist += ['\t%s: %s,' % i for i in itemlist[-2:]]
        else:
            strlist = ['\t%s: %s,' % i for i in itemlist]
        return '''%s({
%s
})''' % (self.__class__.__name__, '\n'.join(strlist))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """ Equality of two ordered collections """

        if not isinstance(other, OrderedCollection):
            return False

        if len(self) != len(other):
            return False

        for oc in zip(self, other):
            if oc[0] != oc[1]:
                return False

        return True

    def __ne__(self, other):
        'Check if two ordered collections are not equal (!= operator)'

        if self == other:
            return False
        else:
            return True

    def __getstate__(self):
        '''
            Used by pickle.dump() and pickle.dumps()
            Notes:
            - Dynamically set instance methods cannot be pickled methods.
              They should not be present in the resulting dict.
            - self.callbacks contains keys that are instance methods,
              and we would like to save them somehow.
        '''
        ret = dict([(k, v) for k, v in self.__dict__.iteritems()
                    if type(v) != types.MethodType
                    and k not in ('callbacks',)])

        callbacks = [((k.im_self, k.im_func.func_name), v)
                     for k, v in self.callbacks.items()]
        ret['callbacks'] = callbacks

        return ret

    def __setstate__(self, d):
        '''
            Used by pickle.load() and pickle.loads()
            Note: We will need to explicitly reconstruct any instance methods
                  that were dynamically set in __init__()
        '''
        d['callbacks'] = dict([(getattr(*obj), name)
                               for obj, name in d['callbacks']])
        self.__dict__ = d

        # reconstruct our dynamically set methods.
        # let's see what we need to do after some testing.

    def to_dict(self, json_='webapi'):
        '''
        Method takes the instance of ordered collection and outputs a dict with
        two fields:
            dtype: associated dtype for each object in the order in which
                it is added
            items: contains a list of tuples containing -
                (importable object name as string, index into collection):
                [(object, 0), (object, 1)]
                The index is always going to be range(number of objects)
            id: a list of IDs for each object. This is not part of the items
                tuple because serialize/deserialize to/from JSON for webapi
                versus saving data out is different

        '''
        if json_ == 'save':
            data = {'dtype': self.dtype,
                    'items': []}
        else:
            data = []

        for count, obj in enumerate(self):
            if json_ == 'save':
                try:
                    obj_type = \
                        '{0.__module__}.{0.__class__.__name__}'.format(obj)
                except AttributeError:
                    obj_type = '{0.__class__.__name__}'.format(obj)

                data['items'].append((obj_type, count))

            else:
                if hasattr(obj, 'id'):
                    data.append(obj.id)
                else:
                    data.append(id(obj))

        return data

    def register_callback(self, callback,
                          events=('add', 'remove', 'replace')):
        if not isinstance(events, (list, tuple)):
            events = (events, )

        for event in events:
            if event not in ('add', 'remove', 'replace'):
                raise ValueError("Events must be either "
                                 "('add', 'remove', 'replace'). "
                                 "{0} is not supported".format(event))

        self.callbacks[callback] = events

    def fire_event(self, event, obj_):
        for (callback, reg_event) in self.callbacks.items():
            if event in reg_event:
                callback(obj_)  # this should be all that is required
