# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/013_data.core.ipynb (unless otherwise specified).

__all__ = ['NumpyTensor', 'ToNumpyTensor', 'TSTensor', 'ToTSTensor', 'show_tuple', 'TSLabelTensor', 'TSMaskTensor',
           'ToFloat', 'ToInt', 'TSClassification', 'TSRegression', 'TSForecasting', 'TSMultiLabelClassification',
           'NumpyTensorBlock', 'TSTensorBlock', 'TorchDataset', 'NumpyDataset', 'TSDataset', 'NoTfmLists',
           'TSTfmdLists', 'NumpyDatasets', 'tscoll_repr', 'TSDatasets', 'add_ds', 'NumpyDataLoader', 'TSDataLoader',
           'NumpyDataLoaders', 'TSDataLoaders', 'get_best_dl_params', 'get_best_dls_params', 'get_ts_dls', 'get_ts_dl',
           'get_subset_dl', 'get_tsimage_dls']

# Cell
from ..imports import *
from ..utils import *
from .validation import *
from .external import *
from .tabular import *
from .mixed import *

# Cell
from matplotlib.ticker import PercentFormatter
import matplotlib.colors as mcolors

# Cell
class NumpyTensor(TensorBase):
    "Returns a `tensor` with subclass `NumpyTensor` that has a show method"

    def __new__(cls, o, **kwargs):
        res = cast(o, cls)
        for k,v in kwargs.items(): setattr(res, k, v)
        return res

    @property
    def data(self): return cast(self, Tensor).data

    def __repr__(self):
        if self.ndim > 0: return f'NumpyTensor(shape:{tuple(self.shape)}, device={self.device})'
        else: return f'NumpyTensor([{self}], device={self.device})'


    def show(self, ax=None, ctx=None, title=None, **kwargs):
        if self.ndim == 0: return str(self)
        elif self.ndim != 2: self = type(self)(to2d(self))
        if not isinstance(self,np.ndarray): self = self.detach().cpu().numpy()
        ax = ifnone(ax, ctx)
        if ax is None: _, ax = plt.subplots(**kwargs)
        ax.plot(self.T)
        ax.axis(xmin=0, xmax=self.shape[-1] - 1)
        title_color = kwargs['title_color'] if 'title_color' in kwargs else matplotlib.rcParams['axes.labelcolor']
        if title is not None:
            if is_listy(title): title = str(title)[1:-1]
            ax.set_title(title, weight='bold', color=title_color)
        plt.tight_layout()
        return ax


class ToNumpyTensor(Transform):
    "Transforms an object into NumpyTensor"
    def encodes(self, o): return NumpyTensor(o)

# Cell
class TSTensor(NumpyTensor):
    '''Returns a `tensor` with subclass `TSTensor` that has a show method'''

    @property
    def vars(self):
        return self.shape[-2]

    @property
    def len(self): return self.shape[-1]

    def __repr__(self):
        if self.ndim >= 3:
            return f'TSTensor(samples:{self.shape[-3]}, vars:{self.shape[-2]}, len:{self.shape[-1]}, device={self.device})'
        elif self.ndim == 2:
            return f'TSTensor(vars:{self.shape[-2]}, len:{self.shape[-1]}, device={self.device})'
        elif self.ndim == 1:
            return f'TSTensor(len:{self.shape[-1]}, device={self.device})'
        else: return f'TSTensor([{self}], device={self.device})'


class ToTSTensor(Transform):
    "Transforms an object into TSTensor"
    def encodes(self, o): return TSTensor(o)


@delegates(plt.subplots)
def show_tuple(tup, **kwargs):
    "Display a timeseries plot from a decoded tuple"
    if len(tup) == 1: title = 'unlabeled'
    elif is_listy(tup[1]): title = str(tup[1])[1:-1]
    else: title = str(tup[1])
    tup[0].show(title=title, **kwargs)

# Cell
class TSLabelTensor(NumpyTensor):
    def __repr__(self):
        if self.ndim == 0: return f'{self}'
        else: return f'TSLabelTensor(shape:{tuple(self.shape)})'

class TSMaskTensor(NumpyTensor):
    def __repr__(self):
        if self.ndim == 0: return f'{self}'
        else: return f'TSMaskTensor(shape:{tuple(self.shape)})'

# Cell
class ToFloat(Transform):
    "Transforms an object dtype to float"
    loss_func=MSELossFlat()
    def encodes(self, o:torch.Tensor): return o.float()
    def encodes(self, o): return o.astype(np.float32)
    def decodes(self, o): return TitledFloat(o) if o.ndim==0 else TitledTuple(o_.item() for o_ in o)


class ToInt(Transform):
    "Transforms an object dtype to int"
    def encodes(self, o:torch.Tensor): return o.long()
    def encodes(self, o): return o.astype(np.float32).astype(np.int64)
    def decodes(self, o): return TitledFloat(o) if o.ndim==0 else TitledTuple(o_.item() for o_ in o)


class TSClassification(DisplayedTransform):
    "Vectorized, reversible transform of category string to `vocab` id"
    loss_func,order,vectorized=CrossEntropyLossFlat(),1,True

    def __init__(self, vocab=None, sort=True, add_na=False):
        if vocab is not None: vocab = CategoryMap(vocab, sort=sort, add_na=add_na)
        store_attr()

    def setups(self, dset):
        dset = np.asarray(dset)
        if self.vocab is None and dset is not None: self.vocab = CategoryMap(dset, sort=self.sort, add_na=self.add_na)
        self.c = len(self.vocab)
        self.vocab_keys = np.array(list(self.vocab.o2i.keys()))[:, None]

    def encodes(self, o):
        try:
            return TensorCategory((self.vocab_keys == o).argmax(axis=0))
        except KeyError as e:
            raise KeyError(f"Label '{o}' was not included in the training dataset") from e
    def decodes(self, o):
        return stack([Category(self.vocab[oi]) for oi in o]) if is_iter(o) else Category(self.vocab[o])


class TSRegression(ToFloat):
    "Vectorized transforms an object dtype to float"
    vectorized=True

TSForecasting = ToFloat

# Cell
class TSMultiLabelClassification(Categorize):
    "Reversible combined transform of multi-category strings to one-hot encoded `vocab` id"
    loss_func,order=BCEWithLogitsLossFlat(),1
    def __init__(self, c=None, vocab=None, add_na=False):
        super().__init__(vocab=vocab,add_na=add_na,sort=vocab==None)
        self.c = c

    def setups(self, dsets):
        if not dsets: return
        if self.vocab is None:
            vals = set()
            for b in dsets: vals = vals.union(set(b))
            self.vocab = CategoryMap(list(vals), add_na=self.add_na)
            if self.c is None: self.c = len(self.vocab)
            if not self.c: warn("Couldn't infer the number of classes, please pass a value for `c` at init")

    def encodes(self, o):
        if not all(elem in self.vocab.o2i.keys() for elem in o):
            diff = [elem for elem in o if elem not in self.vocab.o2i.keys()]
            diff_str = "', '".join(diff)
            raise KeyError(f"Labels '{diff_str}' were not included in the training dataset")
        return TensorMultiCategory(one_hot([self.vocab.o2i[o_] for o_ in o], self.c).float())
    def decodes(self, o): return MultiCategory([self.vocab[o_] for o_ in one_hot_decode(o, None)])

# Cell

class NumpyTensorBlock():
    def __init__(self, type_tfms=None, item_tfms=None, batch_tfms=None, dl_type=None, dls_kwargs=None):
        self.type_tfms  =                 L(type_tfms)
        self.item_tfms  = ToNumpyTensor + L(item_tfms)
        self.batch_tfms =                 L(batch_tfms)
        self.dl_type,self.dls_kwargs = dl_type,({} if dls_kwargs is None else dls_kwargs)

class TSTensorBlock():
    def __init__(self, type_tfms=None, item_tfms=None, batch_tfms=None, dl_type=None, dls_kwargs=None):
        self.type_tfms  =              L(type_tfms)
        self.item_tfms  = ToTSTensor + L(item_tfms)
        self.batch_tfms =              L(batch_tfms)
        self.dl_type,self.dls_kwargs = dl_type,({} if dls_kwargs is None else dls_kwargs)

# Cell
class TorchDataset():
    def __init__(self, X, y=None): self.X, self.y = X, y
    def __getitem__(self, idx): return (self.X[idx],) if self.y is None else (self.X[idx], self.y[idx])
    def __len__(self): return len(self.X)


class NumpyDataset():
    def __init__(self, X, y=None, types=None): self.X, self.y, self.types = X, y, types
    def __getitem__(self, idx):
        if self.types is None: return (self.X[idx], self.y[idx]) if self.y is not None else (self.X[idx])
        else: return (self.types[0](self.X[idx]), self.types[1](self.y[idx])) if self.y is not None else (self.types[0](self.X[idx]))
    def __len__(self): return len(self.X)


class TSDataset():
    def __init__(self, X, y=None, types=None, sel_vars=None, sel_steps=None):
        self.X, self.y, self.types = to3darray(X), y, types
        self.sel_vars = ifnone(sel_vars, slice(None))
        self.sel_steps = ifnone(sel_steps,slice(None))
    def __getitem__(self, idx):
        if self.types is None: return (self.X[idx, self.sel_vars, self.sel_steps], self.y[idx]) if self.y is not None else (self.X[idx])
        else:
            return (self.types[0](self.X[idx, self.sel_vars, self.sel_steps]), self.types[1](self.y[idx])) if self.y is not None \
            else (self.types[0](self.X[idx]))
    def __len__(self): return len(self.X)

# Cell
def _flatten_list(l):
    if not is_listy(l) or len(l) == 0: return l
    return [item for sublist in l for item in listify(sublist)]

def _remove_brackets(l):
    return [li if (not li or not is_listy(li) or len(li) > 1) else li[0] for li in l]

class NoTfmLists(TfmdLists):
    def __init__(self, items, tfms=None, splits=None, split_idx=None, types=None, **kwargs):
        self.splits = ifnone(splits, L(np.arange(len(items)).tolist(),[]))
        self._splits = np.asarray(_flatten_list(self.splits))
        store_attr('items,types,split_idx')
        self.tfms = Pipeline(split_idx=split_idx)
    def subset(self, i, **kwargs): return type(self)(self.items, splits=self.splits[i], split_idx=i, do_setup=False, types=self.types, **kwargs)
    def __getitem__(self, it):
        if hasattr(self.items, 'oindex'): return self.items.oindex[self._splits[it]]
        else: return self.items[self._splits[it]]
    def __len__(self): return len(self._splits)
    def __repr__(self): return f"{self.__class__.__name__}: {self.items.__class__.__name__}{(len(self), *self.items.shape[1:])}"
    def _new(self, items, split_idx=None, **kwargs):
        split_idx = ifnone(split_idx, self.split_idx)
        return type(self)(items, split_idx=split_idx, do_setup=False, types=self.types, **kwargs)
    def decode(self, o, **kwargs): return o
    def new_empty(self): return self._new([])

NoTfmLists.train, NoTfmLists.valid = add_props(lambda i,x: x.subset(i))

class TSTfmdLists(TfmdLists):
    def __getitem__(self, it):
        # res = self._get(it)
        if hasattr(self.items, 'oindex'): res = self.items.oindex[it]
        else: res = self.items[it]
        if self._after_item is None: return res
        else: return self._after_item(res)

# Cell
@delegates(Datasets.__init__)
class NumpyDatasets(Datasets):
    "A dataset that creates tuples from X (and y) and applies `tfms` of type item_tfms"
    typs = NumpyTensor,tensor

    def __init__(self, X=None, y=None, items=None, tfms=None, tls=None, n_inp=None, dl_type=None,
                 inplace=True, **kwargs):

        self.tfms, self.inplace = tfms, inplace

        if X is not None:
            if not hasattr(X, '__array__'): X = np.asarray(X)
            elif hasattr(X, "iloc"): X = to3d(X)
        if y is not None:
            if not hasattr(y, '__array__'):  y = np.asarray(y)
            elif hasattr(y, "iloc"): y = toarray(y)

        if tls is None:
            items = tuple((X,)) if y is None else tuple((X, y))

            if tfms is None:
                self.tfms, lts = [None] * len(items), [NoTfmLists] * len(items)
            else:
                self.tfms = _remove_brackets(tfms)
                lts = [NoTfmLists if (t is None and not inplace) else TSTfmdLists if getattr(t, 'vectorized', None) else TfmdLists for t in self.tfms]

            self.tls = L(lt(item, t, **kwargs) for lt,item,t in zip(lts, items, self.tfms))
            self.typs = [type(tl[0]) if isinstance(tl[0], torch.Tensor) else self.typs[i] for i,tl in enumerate(self.tls)]
            self.ptls = L([typ(stack(tl[:])) for i,(tl,typ) in enumerate(zip(self.tls,self.typs))]) if inplace else self.tls
        else:
            self.tls = tls
            self.ptls = L([typ(stack(tl[:])) for i,(tl,typ) in enumerate(zip(self.tls,self.typs))]) if inplace and len(tls[0]) != 0 else tls

        self.n_inp = 1
        if 'splits' in kwargs:
            split_idxs = kwargs['splits']
            try: split_idxs = flatten_list(split_idxs)
            except: pass
        else: split_idxs = L(np.arange(len(self.tls[0])).tolist())
        self.split_idxs = L(split_idxs)

    def __getitem__(self, it):
        if self.inplace:
            return tuple([ptl[it] for ptl in self.ptls])
        else:
            return tuple([typ(stack(ptl[it])) for i,(ptl,typ) in enumerate(zip(self.ptls,self.typs))])

    def subset(self, i):
        if is_indexer(i):
            return type(self)(tls=L([tl.subset(i) for tl in self.tls]), inplace=self.inplace, tfms=self.tfms,
                              splits=None if self.splits is None else self.splits[i], split_idx=i)
        else:
            splits = None if self.splits is None else L(np.arange(len(i)).tolist())
            return type(self)(*self[i], inplace=True, tfms=None, splits=splits, split_idx=ifnone(self.split_idx, 1))

    def __len__(self): return len(self.tls[0])

    def _new(self, X, *args, y=None, **kwargs):
        items = tuple((X,)) if y is None else tuple((X, y))
        return super()._new(items, tfms=self.tfms, do_setup=False, **kwargs)

    def show_at(self, idx, **kwargs):
        self.show(self[idx], **kwargs)
        plt.show()

    def __repr__(self): return tscoll_repr(self)


def tscoll_repr(c, max_n=10):
    "String repr of up to `max_n` items of (possibly lazy) collection `c`"
    _len = len(c)
    if _len == 0: return coll_repr(c)
    if c.split_idx is None: c = c.subset(0)
    return f'(#{_len}) {L(c[i] for i in range(min(len(c), max_n)))} ...]'

# Cell
@delegates(NumpyDatasets.__init__)
class TSDatasets(NumpyDatasets):
    """A dataset that creates tuples from X (and optionally y) and applies `item_tfms`"""

    typs = TSTensor,tensor
    def __init__(self, X=None, y=None, items=None, sel_vars=None, sel_steps=None, tfms=None, tls=None, n_inp=None, dl_type=None,
                 inplace=True, **kwargs):

        self.sel_vars, self.sel_steps, self.tfms, self.inplace = ifnone(sel_vars, slice(None)), ifnone(sel_steps,slice(None)), tfms, inplace

        if X is not None:
            if not hasattr(X, '__array__'): X = np.asarray(X)
            elif hasattr(X, "iloc"): X = to3d(X)
        if y is not None:
            if not hasattr(y, '__array__'):  y = np.asarray(y)
            elif hasattr(y, "iloc"): y = toarray(y)

        if tls is None:
            items = tuple((X,)) if y is None else tuple((X, y))

            if tfms is None:
                self.tfms, lts = [None] * len(items), [NoTfmLists] * len(items)
            else:
                self.tfms = _remove_brackets(tfms)
                lts = [NoTfmLists if (t is None and not inplace) else TSTfmdLists if getattr(t, 'vectorized', None) else TfmdLists for t in self.tfms]

            self.tls = L(lt(item, t, **kwargs) for lt,item,t in zip(lts, items, self.tfms))
            self.typs = [type(tl[0]) if isinstance(tl[0], torch.Tensor) else self.typs[i] for i,tl in enumerate(self.tls)]
            self.ptls = L([typ(stack(tl[:]))[...,self.sel_vars, self.sel_steps] if i==0 else typ(stack(tl[:])) \
                            for i,(tl,typ) in enumerate(zip(self.tls,self.typs))]) if inplace else self.tls
        else:
            self.tls = tls
            self.ptls = L([typ(stack(tl[:]))[...,self.sel_vars, self.sel_steps] if i==0 else typ(stack(tl[:])) \
                            for i,(tl,typ) in enumerate(zip(self.tls,self.typs))]) if inplace and len(tls[0]) != 0 else tls

        self.n_inp = 1
        if 'splits' in kwargs:
            split_idxs = kwargs['splits']
            try: split_idxs = flatten_list(split_idxs)
            except: pass
        else: split_idxs = L(np.arange(len(self.tls[0])).tolist())
        self.split_idxs = L(split_idxs)

    def __getitem__(self, it):
        if self.inplace:
            return tuple([ptl[it] for ptl in self.ptls])
        else:
            return tuple([typ(stack(ptl[it]))[...,self.sel_vars, self.sel_steps] if i==0 else typ(stack(ptl[it])) \
                          for i,(ptl,typ) in enumerate(zip(self.ptls,self.typs))])

    def subset(self, i):
        if is_indexer(i):
            return type(self)(tls=L([tl.subset(i) for tl in self.tls]), inplace=self.inplace, tfms=self.tfms,
                              sel_vars=self.sel_vars, sel_steps=self.sel_steps, splits=None if self.splits is None else self.splits[i], split_idx=i)
        else:
            splits = None if self.splits is None else L(np.arange(len(i)).tolist())
            return type(self)(*self[i], inplace=True, tfms=None,
                              sel_vars=self.sel_vars, sel_steps=self.sel_steps, splits=splits, split_idx=ifnone(self.split_idx, 1))

# Cell
def add_ds(dsets, X, y=None, inplace=True):
    "Create test datasets from X (and y) using validation transforms of `dsets`"
    items = tuple((X,)) if y is None else tuple((X, y))
    with_labels = False if y is None else True
    if isinstance(dsets, Datasets):
        tls = dsets.tls if with_labels else dsets.tls[:dsets.n_inp]
        new_tls = L([tl._new(item, split_idx=1) for tl,item in zip(tls, items)])
        return type(dsets)(tls=new_tls)
    elif isinstance(dsets, TfmdLists):
        new_tl = dsets._new(items, split_idx=1)
        return new_tl
    else:
        raise Exception(f"Expected a `Datasets` or a `TfmdLists` but got {dsets.__class__.__name__}")

@patch
def add_dataset(self:NumpyDatasets, X, y=None, inplace=True):
    return add_ds(self, X, y=y, inplace=inplace)

@patch
def add_test(self:NumpyDatasets, X, y=None, inplace=True):
    return add_ds(self, X, y=y, inplace=inplace)

@patch
def add_unlabeled(self:NumpyDatasets, X, inplace=True):
    return add_ds(self, X, y=None, inplace=inplace)

# Cell
@patch
def _one_pass(self:TfmdDL):
    b = self.do_batch([self.do_item(0)])
    if self.device is not None: b = to_device(b, self.device)
    its = self.after_batch(b)
    self._n_inp = 1 if not isinstance(its, (list,tuple)) or len(its)==1 else len(its)-1
    self._types = explode_types(its)

# Cell
_batch_tfms = ('after_item','before_batch','after_batch')

@delegates(TfmdDL.__init__)
class NumpyDataLoader(TfmdDL):
    idxs = None
    do_item = noops # create batch returns indices
    def __init__(self, dataset, bs=64, shuffle=True, drop_last=True, num_workers=None, verbose=False, do_setup=True, batch_tfms=None,
                 weights=None, partial_n=None, **kwargs):
        '''batch_tfms == after_batch (either can be used)'''

        if num_workers is None: num_workers = min(16, defaults.cpus)
        for nm in _batch_tfms:
            if nm == 'after_batch':
                if batch_tfms is not None: kwargs[nm] = Pipeline(batch_tfms if is_listy(batch_tfms) else [batch_tfms])
                else: kwargs[nm] = Pipeline(kwargs.get(nm,None))
            else: kwargs[nm] = Pipeline(kwargs.get(nm,None))
        bs = min(bs, len(dataset))
        if is_listy(partial_n): partial_n = partial_n[0]
        if isinstance(partial_n, float): partial_n = int(round(partial_n * len(dataset)))
        if partial_n is not None: bs = min(bs, partial_n)
        if weights is not None: weights = weights / weights.sum()
        self.weights, self.partial_n = weights, partial_n
        super().__init__(dataset, bs=bs, shuffle=shuffle, drop_last=drop_last, num_workers=num_workers, **kwargs)
        if do_setup:
            for nm in _batch_tfms:
                pv(f"Setting up {nm}: {kwargs[nm]}", verbose)
                kwargs[nm].setup(self)

    @delegates(DataLoader.new)
    def new(self, dataset=None, cls=None, **kwargs):
        after_batch = self.after_batch
        res = super().new(dataset, cls, **kwargs)
        self.after_batch = res.after_batch
        if not hasattr(self, '_n_inp') or not hasattr(self, '_types'):
            try:
                self._one_pass()
                res._n_inp,res._types = self._n_inp,self._types
            except: print("Could not do one pass in your dataloader, there is something wrong in it")
        else: res._n_inp,res._types = self._n_inp,self._types
        return res

    def new_dl(self, X, y=None):
        assert X.ndim == 3, "You must pass an X with 3 dimensions [batch_size x n_vars x seq_len]"
        if y is not None and not is_array(y) and not is_listy(y): y = [y]
        new_dloader = self.new(self.dataset.add_dataset(X, y=y))
        return new_dloader

    def create_batch(self, b):
        if self.shuffle:
            it = b
            if hasattr(it, 'sort'): it.sort()
        else: it = slice(b[0], b[0] + self.bs)
        self.idxs = L(it)
        if hasattr(self, "split_idxs"): self.input_idxs = self.split_idxs[it]
        else: self.input_idxs = self.idxs
        return self.dataset[it]

    def create_item(self, s):
        if self.indexed: return self.dataset[s or 0]
        elif s is None:  return next(self.it)
        else: raise IndexError("Cannot index an iterable dataset numerically - must use `None`.")

    def get_idxs(self):
        if self.n==0: return []
        if self.partial_n is not None: n = min(self.partial_n, self.n)
        else: n = self.n
        if self.weights is not None:
            return np.random.choice(self.n, n, p=self.weights)
        idxs = Inf.count if self.indexed else Inf.nones
        if self.n is not None:
            idxs = np.arange(self.n)
            if self.partial_n is not None:
                idxs = np.random.choice(idxs, n, False)
        if self.shuffle: idxs = self.shuffle_fn(idxs)
        return idxs

    def shuffle_fn(self, idxs):
        return np.random.permutation(idxs)

    def unique_batch(self, max_n=9):
        old_bs = self.bs
        self.bs = 1
        old_get_idxs = self.get_idxs
        self.get_idxs = lambda: Inf.zeros
        out_len = len(self.items)
        types = self.dataset.types
        x, y = [], []
        for _ in range(max_n):
            out = self.one_batch()
            if out_len == 2:
                x.extend(out[0])
                y.extend(out[1])
            else:
                x.extend(out)
        b = (types[0](stack(x)), types[1](stack(y))) if out_len == 2 else (types[0](stack(x)), )
        self.bs = old_bs
        self.get_idxs = old_get_idxs
        return b


    @delegates(plt.subplots)
    def show_batch(self, b=None, ctxs=None, max_n=9, nrows=3, ncols=3, figsize=None, unique=False, sharex=True, sharey=False, decode=False, **kwargs):
        if unique:
            b = self.unique_batch(max_n=max_n)
            sharex, sharey = True, True
        elif b is None: b = self.one_batch()
        if not decode:                                        # decode = False allows you to see the data as seen by the model
            after_batch = self.after_batch
            self.after_batch = fastcore.transform.Pipeline()
            db = self.decode_batch(b, max_n=max_n)
            self.after_batch = after_batch
        else:
            db = self.decode_batch(b, max_n=max_n)
        ncols = min(ncols, math.ceil(len(db) / ncols))
        nrows = min(nrows, math.ceil(len(db) / ncols))
        max_n = min(max_n, len(db), nrows*ncols)
        if figsize is None: figsize = (ncols*6, math.ceil(max_n/ncols)*4)
        if ctxs is None: ctxs = get_grid(max_n, nrows=nrows, ncols=ncols, figsize=figsize, sharex=sharex, sharey=sharey, **kwargs)
        for i,ctx in enumerate(ctxs): show_tuple(db[i], ctx=ctx)

    @delegates(plt.subplots)
    def show_results(self, b, preds, ctxs=None, max_n=9, nrows=3, ncols=3, figsize=None, **kwargs):
        t = self.decode_batch(b, max_n=max_n)
        p = self.decode_batch((b[0],preds), max_n=max_n)
        if figsize is None: figsize = (ncols*6, max_n//ncols*4)
        if ctxs is None: ctxs = get_grid(min(len(t), nrows*ncols), nrows=None, ncols=ncols, figsize=figsize, **kwargs)
        for i,ctx in enumerate(ctxs):
            title = f'True: {t[i][1]}\nPred: {p[i][1]}'
            color = 'green' if t[i][1] == p[i][1] else 'red'
            t[i][0].show(ctx=ctx, title=title, title_color=color)

    @delegates(plt.subplots)
    def show_dist(self, figsize=None, color=None, **kwargs):
        if self.c == 0:
            print('\nunlabeled dataset.\n')
            return
        b = self.one_batch()
        i = getattr(self, 'n_inp', 1 if len(b)==1 else len(b)-1)
        yb = b[i:][0]
        if color == "random": color = random_shuffle(L(mcolors.CSS4_COLORS.keys()))
        elif color is None: color = ['m', 'orange', 'darkblue', 'lightgray']
        figsize = ifnone(figsize, (8, 6))
        plt.figure(figsize=figsize, **kwargs)
        ax = plt.axes()
        ax.set_axisbelow(True)
        plt.grid(color='gainsboro', linewidth=.1)
        plt.title('Target distribution in a single batch', fontweight='bold')
        if self.cat:
            if yb.ndim == 1:
                yb = yb.flatten().detach().cpu().numpy()
                data = np.unique(yb, return_counts=True)[1]
                data = data / np.sum(data)
            else:
                yb = yb.detach().cpu().numpy()
                data = yb.mean(0)
            plt.bar(self.vocab, data, color=color, edgecolor='black')
            plt.xticks(self.vocab)
        else:
            yb = yb.flatten().detach().cpu().numpy()
            weights=np.ones(len(yb)) / len(yb)
            plt.hist(yb, bins=min(len(yb) // 2, 100), weights=weights, color='violet', edgecolor='black')
        plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
        plt.show()

    @property
    def c(self):
        if len(self.dataset) == 0: return 0
        if hasattr(self, "vocab"):
            return len(self.vocab)
        else:
            return self.d if not is_listy(self.d) else reduce(lambda x, y: x * y, self.d, 1)

    @property
    def d(self):
        if len(self.dataset) == 0: return 0
        b = self.one_batch()
        if len(b) == 1: return 0
        i = getattr(self, 'n_inp', 1 if len(b)==1 else len(b)-1)
        yb = b[i:]
        if len(yb[0][0].shape) == 0: return 1
        elif len(yb[0][0].shape) == 1: return yb[0][0].shape[0]
        else: return list(yb[0][0].shape)

    @property
    def cat(self): return hasattr(self, "vocab")

    @property
    def cws(self):
        if self.cat:
            if self.ptls[-1].ndim == 2: # one hot encoded
                pos_per_class = self.ptls[-1].sum(0)
                neg_per_class = (len(self.ptls[-1]) - pos_per_class)
                pos_weights = neg_per_class / pos_per_class
                pos_weights[pos_weights == float('inf')] = 0
                return torch.Tensor(pos_weights).to(self.device)
            else:
                counts = torch.unique(self.ptls[-1].flatten(), return_counts=True, sorted=True)[-1]
                iw = (counts.sum() / counts)
                return (iw / iw.sum()).to(self.device)
        else: return None

    @property
    def class_priors(self):
        if self.cws is not None:
            cp = 1. / (self.cws + 1e-8)
            return (cp / cp.sum()).to(self.device)
        else: return None


class TSDataLoader(NumpyDataLoader):
    @property
    def vars(self):
        if len(self.dataset) == 0: return 0
        b = self.one_batch()
        i = getattr(self, 'n_inp', 1 if len(b)==1 else len(b)-1)
        xb = b[:i]
        if hasattr(xb[0], 'vars'): return xb[0].vars
        if xb[0].ndim >= 4: return xb[0].shape[-3]
        else: return xb[0].shape[-2]
    @property
    def len(self):
        if len(self.dataset) == 0: return 0
        b = self.one_batch()
        i = getattr(self, 'n_inp', 1 if len(b)==1 else len(b)-1)
        xb = b[:i]
        if hasattr(xb[0], 'len'): return xb[0].len
        if xb[0].ndim >= 4: return xb[0].shape[-2:]
        else: return xb[0].shape[-1]

# Cell
_batch_tfms = ('after_item','before_batch','after_batch')

class NumpyDataLoaders(DataLoaders):
    _xblock = NumpyTensorBlock
    _dl_type = NumpyDataLoader
    def __init__(self, *loaders, path='.', device=None):
        self.loaders, self.path = list(loaders), Path(path)
        self.device = ifnone(device, default_device())

    def new_dl(self, X, y=None):
        assert X.ndim == 3, "You must pass an X with 3 dimensions [batch_size x n_vars x seq_len]"
        if y is not None and not is_array(y) and not is_listy(y): y = [y]
        new_dloader = self.new(self.dataset.add_dataset(X, y=y))
        return new_dloader

    @delegates(plt.subplots)
    def show_dist(self, figsize=None, **kwargs): self.loaders[0].show_dist(figsize=figsize, **kwargs)

    def decoder(self, o):
        if isinstance(o, tuple): return self.decode(o)
        if o.ndim <= 1: return self.decodes(o)
        else: return L([self.decodes(oi) for oi in o])

    def decode(self, b):
        return to_cpu(self.after_batch.decode(self._retain_dl(b)))


    @classmethod
    @delegates(DataLoaders.from_dblock)
    def from_numpy(cls, X, y=None, splitter=None, valid_pct=0.2, seed=0, item_tfms=None, batch_tfms=None, **kwargs):
        "Create timeseries dataloaders from arrays (X and y, unless unlabeled)"
        if splitter is None: splitter = RandomSplitter(valid_pct=valid_pct, seed=seed)
        getters = [ItemGetter(0), ItemGetter(1)] if y is not None else [ItemGetter(0)]
        dblock = DataBlock(blocks=(cls._xblock, CategoryBlock),
                           getters=getters,
                           splitter=splitter,
                           item_tfms=item_tfms,
                           batch_tfms=batch_tfms)

        source = itemify(X) if y is None else itemify(X,y)
        return cls.from_dblock(dblock, source, **kwargs)

    @classmethod
    def from_dsets(cls, *ds, path='.', bs=64, num_workers=0, batch_tfms=None, device=None, shuffle_train=True, drop_last=True,
                   weights=None, partial_n=None, **kwargs):
        device = ifnone(device, default_device())
        if batch_tfms is not None and not isinstance(batch_tfms, list): batch_tfms = [batch_tfms]
        default = (shuffle_train,) + (False,) * (len(ds)-1)
        defaults = {'shuffle': default, 'drop_last': default}
        kwargs = merge(defaults, {k: tuplify(v, match=ds) for k,v in kwargs.items()})
        kwargs = [{k: v[i] for k,v in kwargs.items()} for i in range_of(ds)]
        if not is_listy(bs): bs = [bs]
        if len(bs) != len(ds): bs = bs * len(ds)
        if weights is None: weights = [None] * len(ds)
        if not is_listy(partial_n): partial_n = [partial_n]
        if len(partial_n) != len(ds): partial_n = partial_n * len(ds)
        loaders = [cls._dl_type(d, bs=b, num_workers=num_workers, batch_tfms=batch_tfms, weights=w, partial_n=n, **k) \
                   for d,k,b,w,n in zip(ds, kwargs, bs, weights, partial_n)]
        return cls(*loaders, path=path, device=device)


class TSDataLoaders(NumpyDataLoaders):
    _xblock = TSTensorBlock
    _dl_type = TSDataLoader

# Cell
def get_best_dl_params(dl, n_iters=10, num_workers=[0, 1, 2, 4, 8], pin_memory=False, prefetch_factor=[2, 4, 8], return_best=True, verbose=True):

    if not torch.cuda.is_available():
        num_workers = 0
    n_iters = min(n_iters, len(dl))
    if not return_best: verbose = True

    nw = dl.fake_l.num_workers
    pm = dl.fake_l.pin_memory
    pf = dl.fake_l.prefetch_factor

    try:
        best_nw = nw
        best_pm = pm
        best_pf = pf

        # num_workers
        if not num_workers: best_nw = nw
        elif isinstance(num_workers, Integral): best_nw = num_workers
        else:
            best_time = np.inf
            for _nw in num_workers:
                dl.fake_l.num_workers = _nw
                timer.start(False)
                for i, _ in enumerate(dl):
                    if i == n_iters - 1:
                        t = timer.stop().total_seconds() / (i + 1)
                        pv(f'   num_workers: {_nw:2}  pin_memory: {pm!s:^5}  prefetch_factor: {pf:2}  -  time: {1_000 * t/n_iters:8.3f} ms/iter', verbose)
                        if t < best_time:
                            best_nw = _nw
                            best_time = t
                        break
        dl.fake_l.num_workers = best_nw


        # pin_memory
        if not pin_memory: best_pm = pm
        elif isinstance(pin_memory, bool): best_pm = pin_memory
        else:
            best_time = np.inf
            if not pin_memory: pin_memory = [pm]
            for _pm in pin_memory:
                dl.fake_l.pin_memory = _pm
                timer.start(False)
                for i, _ in enumerate(dl):
                    if i == n_iters - 1:
                        t = timer.stop().total_seconds() / (i + 1)
                        pv(f'   num_workers: {best_nw:2}  pin_memory: {_pm!s:^5}  prefetch_factor: {pf:2}  -  time: {1_000 * t/n_iters:8.3f} ms/iter',
                           verbose)
                        if t < best_time:
                            best_pm = _pm
                            best_time = t
                        break
        dl.fake_l.pin_memory = best_pm

        # prefetch_factor
        if not prefetch_factor: best_pf = pf
        elif isinstance(prefetch_factor, Integral): best_pf = prefetch_factor
        else:
            best_time = np.inf
            if not prefetch_factor: prefetch_factor = [pf]
            for _pf in prefetch_factor:
                dl.fake_l.prefetch_factor = _pf
                timer.start(False)
                for i, _ in enumerate(dl):
                    if i == n_iters - 1:
                        t = timer.stop().total_seconds() / (i + 1)
                        pv(f'   num_workers: {best_nw:2}  pin_memory: {best_pm!s:^5}  prefetch_factor: {_pf:2}  -  time: {1_000 * t/n_iters:8.3f} ms/iter',
                           verbose)
                        if t < best_time:
                            best_pf = _pf
                            best_time = t
                        break
        dl.fake_l.prefetch_factor = best_pf

    except KeyboardInterrupt:
        dl.fake_l.num_workers = best_nw if return_best else nw
        dl.fake_l.pin_memory = best_pm if return_best else pm
        dl.fake_l.prefetch_factor = best_pf if return_best else pf

    if not return_best:
        dl.fake_l.num_workers = nw
        dl.fake_l.pin_memory = pm
        dl.fake_l.prefetch_factor = pf

    if verbose:
        print('\n   best dl params:')
        print(f'       best num_workers    : {best_nw}')
        print(f'       best pin_memory     : {best_pm}')
        print(f'       best prefetch_factor: {best_pf}')
        print(f'       return_best         : {return_best}')
        print('\n')

    return dl

def get_best_dls_params(dls, n_iters=10, num_workers=[0, 1, 2, 4, 8], pin_memory=False, prefetch_factor=[2, 4, 8], return_best=True, verbose=True):

    for i in range(len(dls.loaders)):
        try:
            print(f'\nDataloader {i}\n')
            dls.loaders[i] = get_best_dl_params(dls.loaders[i], n_iters=n_iters, num_workers=num_workers, pin_memory=pin_memory,
                                            prefetch_factor=prefetch_factor, return_best=return_best, verbose=verbose)
        except KeyboardInterrupt: pass
    return dls

# Cell
def get_ts_dls(X=None, y=None, cat=None, cont=None, df=None, splits=None, sel_vars=None, sel_steps=None, tfms=None, procs=[Categorify, FillMissing, Normalize],
               inplace=True, path='.', bs=64, batch_tfms=None, num_workers=0, device=None, shuffle_train=True, drop_last=True, weights=None, partial_n=None,
                **kwargs):
    if isinstance(X, (str, pd.core.indexes.base.Index)) or (isinstance(X, list) and (isinstance(X[0], str) or is_indexer(X[0]))):
        X = to3darray(df[str2index(X)])
    if isinstance(y, (str, pd.core.indexes.base.Index)) or (isinstance(y, list) and (isinstance(y[0], str) or is_indexer(y[0]))):
        y_names = str2list(y)
        y = df[str2index(y)].values
    else: y_names = None

    if splits is None: splits = (L(np.arange(len(X)).tolist()), L([]))

    # ts_dls
    dsets = TSDatasets(X, y, splits=splits, sel_vars=sel_vars, sel_steps=sel_steps, tfms=tfms, inplace=inplace)
    if weights is not None:
        assert len(X) == len(weights)
        if splits is not None: weights = [weights[split] if i == 0 else None for i,split in enumerate(splits)] # weights only applied to train set
    dls   = TSDataLoaders.from_dsets(dsets.train, dsets.valid, path=path, bs=bs, batch_tfms=batch_tfms, num_workers=num_workers,
                                     device=device, shuffle_train=shuffle_train, drop_last=drop_last, weights=weights, partial_n=partial_n)
    if cat is None and cont is None: return dls

    # tab dls
    c, d = dls.c, dls.d
    cat, cont = str2index(cat),str2index(cont)
    cols = []
    for _cols in [cat, cont, y_names]:
        if _cols is not None: cols.extend(_cols)
    cols = list(set(cols))
    if is_listy(bs): bs = min(bs)
    if splits is not None: bs = min(len(splits[0]), bs)
    else: bs = min(len(df), bs)
    tab_dls = get_tabular_dls(df[cols], procs=procs, cat_names=cat, cont_names=cont, y_names=y_names, splits=splits, bs=bs, device=device, **kwargs)
    mixed_dls = combine_dls(dls, tab_dls, path=path)
    if cat is not None: cat = len(cat)
    if cont is not None: cont = len(cont)
    for n,v in zip(["c", "d", "cat", "cont", "classes"], [dls.c, dls.d, cat, cont, tab_dls.classes]):
        setattr(mixed_dls, n, v)
    return mixed_dls

def get_ts_dl(X, y=None, sel_vars=None, sel_steps=None, tfms=None, inplace=True,
            path='.', bs=64, batch_tfms=None, num_workers=0, device=None, shuffle_train=True, drop_last=True, weights=None, partial_n=None, **kwargs):
    splits = (L(np.arange(len(X)).tolist()), L([]))
    dsets = TSDatasets(X, y, splits=splits, sel_vars=sel_vars, sel_steps=sel_steps, tfms=tfms, inplace=inplace, **kwargs)
    if not is_listy(partial_n): partial_n = [partial_n]
    dls   = TSDataLoaders.from_dsets(dsets.train, path=path, bs=bs, batch_tfms=batch_tfms, num_workers=num_workers,
                                     device=device, shuffle_train=shuffle_train, drop_last=drop_last, weights=weights, partial_n=partial_n, **kwargs)
    return dls.train

get_tsimage_dls = get_ts_dls

def get_subset_dl(dl, idxs): return dl.new(dl.dataset.subset(idxs))