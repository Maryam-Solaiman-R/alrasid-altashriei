from abc import ABC, abstractmethod

class SourceAdapter(ABC):
    @abstractmethod
    async def fetch_document(self, url: str) -> dict:
        raise NotImplementedError
