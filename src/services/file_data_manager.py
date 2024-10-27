import csv
import os
import pandas as pd
import zipfile
import chardet
from pandas import DataFrame


class FileDataManager:

    def open_file(self, path: str, mime_type: str) -> DataFrame:
        actions = {
            "text/csv": self._read_csv_file,
            "text/plain": self._read_csv_file,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": self._read_excel_file,
            "application/vnd.ms-excel": self._read_excel_file,
            "application/json": self._read_json_file,
            "application/xml": self._read_xml_file
        }

        return actions.get(mime_type, self._unsupported_file)(path)

    @staticmethod
    def get_encoding(path: str) -> str:
        with open(path, "rb") as file:
            encoding = chardet.detect(file.read())["encoding"]
        return encoding

    @staticmethod
    def unpack_file(file_path: str, extraction_path: str):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extraction_path)

    @staticmethod
    def delete_file(file_path: str):
        os.remove(file_path)

    def _read_csv_file(self, path: str) -> DataFrame:
        encoding = self.get_encoding(path)
        with open(path, 'r', encoding=encoding) as f:
            amostra = f.readline()  # Lê uma amostra para detecção
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(amostra).delimiter

        return pd.read_csv(path, delimiter=delimiter, encoding=encoding, dtype=str)

    @staticmethod
    def _read_excel_file(path: str) -> DataFrame:
        return pd.read_excel(path)

    @staticmethod
    def _read_json_file(path: str) -> DataFrame:
        return pd.read_json(path)

    @staticmethod
    def _read_xml_file(path: str) -> DataFrame:
        return pd.read_xml(path)

    @staticmethod
    def _unsupported_file(path: str):
        return {"error": f"Unsupported file type for {path}"}

    @staticmethod
    def create_sample(dataframe: DataFrame, n: int = 10) -> DataFrame:
        return dataframe.sample(n=n)

    @staticmethod
    def convert_dataframe_to_json(dataframe: DataFrame) -> dict:
        headers = dataframe.columns.tolist()
        return {
            "headers": headers,
            "values": dataframe.to_dict(orient="records")
        }
