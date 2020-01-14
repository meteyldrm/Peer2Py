import uuid
import os
import sys

class File:
	class _Defaults:
		tempExtension = "tmp"
	def __init__(self, fileName = None, fileExt = None, directory = None, mode = "r+"):
		self._fn = fileName
		self._fe = fileExt
		self._d = directory
		self.fileName = None
		self.directory = None
		self.fullFilePath = None
		self.assimilatedTempFile = None
		self._file = None
		self._mode = mode

	def _assimilateOverride(self, func):
		def wrapper():
			name = func.__name__
			if self.assimilatedTempFile is not None:
				return getattr(self.assimilatedTempFile, name)()
			else:
				return getattr(self, name)()
		return wrapper

	def generateFileInformation(self, fileName, fileExt, directory):
		if (ext := fileExt) is not None:
			fileExt = ext
		else:
			fileExt = self._Defaults.tempExtension

		if (name := fileName) is not None:
			fileName = name + "." + fileExt
		else:
			name = str(uuid.uuid1()).replace("-", "")
			fileName = name + "." + fileExt

		if directory is None:
			directory = sys.path[0]

		return fileName, fileExt, directory

	def __enter__(self):
		self.fileName, fileExt, self.directory = self.generateFileInformation(self._fn, self._fe, self._d)
		self.fullFilePath = os.path.join(self.directory, self.fileName)

		if self.fileName.endswith("." + self._Defaults.tempExtension):
			self.assimilatedTempFile = Temp.assimilate(self)
		elif os.path.exists(self.fullFilePath):
			os.chdir(self.directory)
			self._file = open(self.fileName, self._mode)
		else:
			self._create()
			self._file = open(self.fileName, self._mode)

	@_assimilateOverride
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()

	@_assimilateOverride
	def _create(self):
		os.chdir(self.directory)
		open(self.fileName, "w+").close()

	@_assimilateOverride
	def seek(self, index = None, reference = None):
		if index is None and reference is None:
			index = 0
			reference = 1
		if not (index == 0 and reference == 1):
			if self._file.seekable:
				return self._file.seek(index, reference)

	@_assimilateOverride
	def read(self, size = 0, index = None, reference = None):
		self.seek(index, reference)
		if size == 0:
			return self._file.read()
		else:
			return self._file.read(size)

	@_assimilateOverride
	def append(self, text, addNewLine = False):
		if addNewLine:
			text = text + "/n"
		return self.write(text, 0, 2)

	@_assimilateOverride
	def write(self, text, index, reference):
		if self._mode in ["a+", "ab+"]:
			index = 0
			reference = 2
		self.seek(index, reference)
		return self._file.write(text)

	@_assimilateOverride
	def close(self):
		if not self._file.closed:
			return self._file.close()
		else:
			return None

	@_assimilateOverride
	def delete(self):
		self._file.close()
		return os.unlink(self.fullFilePath)

class Temp(File):
	appendMode = True

	def __init__(self, fileName = None, fileExt = None, directory = None, _assimilation = False):
		self._assimilation = _assimilation
		if not _assimilation and isinstance(_assimilation, bool):
			super().__init__(fileName, fileExt, directory)
			self.fileName, fileExt, self.directory = self.generateFileInformation(self._fn, self._fe, self._d)
			self.fullFilePath = os.path.join(self.directory, self.fileName)
		elif isinstance(_assimilation, File):
			self.fileName = _assimilation.fileName
			self.fullFilePath = _assimilation.fullFilePath
			self.directory = _assimilation.directory

	@classmethod
	def assimilate(cls, superclass):
		return cls(_assimilation = superclass)

	def __enter__(self):
		self._create()
		self._file = open(self.fullFilePath, "a+") #Open file upon initialization

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.delete()

	def _create(self):
		os.chdir(self.directory)
		open(self.fileName, "w+").close()

	def seek(self, index = None, reference = None):
		if index is None and reference is None:
			index = 0
			reference = 1
		if not (index == 0 and reference == 1):
			if self._file.seekable:
				return self._file.seek(index, reference)

	def read(self, size = 0, index = None, reference = None):
		self.seek(index, reference)
		return self.read(size)

	def append(self, text, addNewLine = False):
		if self.appendMode:
			if addNewLine:
				text = text + "/n"
			return self._file.write(text)
		else:
			if addNewLine:
				text = text + "/n"
			return self.write(text, 0, 2)

	def write(self, text, index, reference):
		if self.appendMode:
			self._file.close()
			os.chdir(self.directory)
			self._file = open(self.fileName, "r+")
			self.appendMode = False
		self.seek(index, reference)
		return self._file.write(text)

	def close(self):
		if not self._file.closed:
			return self._file.close()
		else:
			return None

	def delete(self):
		self.close()
		return os.unlink(self.fullFilePath)