import os
import ssl
import re
import logging
from string import Template
from dotenv import load_dotenv
from irods.session import iRODSSession
from irods.meta import iRODSMeta
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ValidationError
from typing import List, Optional, Dict, Set, ClassVar, Union
from datetime import datetime
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

# schema

schema = {
    "output": {
        "collections": ["Gene", "GeneFull", "Velocyto"],
        "data_objects": ["Barcodes.stats"]
    },
    "Gene": {
        "collections": ["filtered", "raw"],
        "data_objects": ["Features.stats", "Summary.csv", "UMIperCellSorted.txt"]
    },
    "GeneFull": {
        "collections": ["filtered", "raw"],
        "data_objects": ["Features.stats", "Summary.csv", "UMIperCellSorted.txt"]
    },
    "Velocyto": {
        "collections": ["filtered", "raw"],
        "data_objects": ["Features.stats", "Summary.csv"]
    },
    "filtered": {
        "collections": [],
        "data_objects": ["barcodes.tsv.gz", "features.tsv.gz", "matrix.mtx.gz"]
    },
    "raw": {
        "collections": [],
        "data_objects": ["barcodes.tsv.gz", "features.tsv.gz", "matrix.mtx.gz"]
    }
}

# Set up logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),  # Log to file
        logging.StreamHandler()  # Also log to console
    ]
)


class IrodsCollection(BaseModel):
    name: str
    path: str
    create_time: datetime
    modify_time: datetime
    expected_data_objects: Set[str] = Field(default_factory=set)
    expected_collections: Set[str] = Field(default_factory=set)
    expected_metadata_keys: Set[str] = Field(default_factory=set)
    metadata: Dict[str, List[str]] = Field(default_factory=lambda: defaultdict(list) )
    collections: List['IrodsCollection'] = Field(default_factory=list)
    data_objects: List[str] = Field(default_factory=list)

    def __repr__(self):
        return f"IrodsCollection(name='{self.name}', path='{self.path}, create_time='{self.create_time}', modify_time='{self.modify_time}', metadata={self.metadata}, collections={[coll.name for coll in self.collections] if self.collections else None}, data_objects={self.data_objects if self.data_objects else None})"
    
    def __str__(self):
        return "\n".join(
            [
                f"IrodsCollection:",
                f"  Name: {self.name}",
                f"  Path: {self.path}",
                f"  Created: {self.create_time}",
                f"  Modified: {self.modify_time}",
                f"  Metadata: {self.metadata}",
                f"  Collections: {[coll.name for coll in self.collections] if self.collections else None}",
                f"  Data Objects: {self.data_objects if self.data_objects else None}",
            ]
        )
    
    @field_validator("data_objects", "collections", mode="after")
    @classmethod
    def check_files(cls, objects: Optional[List[Union[str,'IrodsCollection']]], info: ValidationInfo) -> Optional[List[str]]:
        field = info.field_name
        object_names = [(irods_object if field == "data_objects" else irods_object.name) for irods_object in objects]
        object_names_set = set(object_names)
        patterns = info.data.get(f"expected_{field}").copy()
        path = info.data.get("path")

        # Check if each data object matches any of the expected file templates
        if patterns:
            for irods_object in object_names:
                for pattern in patterns:
                    if re.fullmatch(pattern, irods_object):
                        patterns.remove(pattern)
                        object_names_set.remove(irods_object)
                        break
            
            # Warn ff there are any expected files left unmatched
            if patterns:
                logging.warning(f"Missing expected files for collection {path}: {patterns}")

            # Warn if there are any data objects left unmatched, raise a validation error
            if object_names_set:
                logging.warning(f"Unexpected data objects for collection {path}: {[irods_object for irods_object in object_names_set]}")
        return objects
    

class STARsoloCollection(IrodsCollection):
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """
        Check that collection name starts with 'SRS', 'GSM' or 'ERS'
        """
        if not re.match(r'^(SRS|GSM|ERS)', name):
            logging.warning(f"Collection name '{name}' does not start with 'SRS', 'GSM' or 'ERS'")
        return name


class DatasetCollection(IrodsCollection):
    collections: List['STARsoloCollection'] = None

    _expected_files: ClassVar[Dict[str, Set[Template]]] = {
        "E-MTAB-": {
            Template("${series}.ena.tsv"),
            Template("${series}.idf.txt"),
            Template("${series}.sdrf.txt")
        },
        "GSE": {
            Template("${series}.family.soft"),
            Template("${series}.(?:ena|sra).tsv"),
        },
        "other": {
            Template("${series}.accessions.tsv"),
            Template("${series}.parsed.tsv"),
            Template("${series}.run.list"),
            Template("${series}.sample.list"),
            Template("${series}.sample_x_run.tsv"),
            Template("${series}*solo_qc*.tsv")
        }
    }

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """
        Check that collection name starts with 'GSE', "E-MTAB-", "EGAD", "PRJEB", "PRJNA" or "HRA"
        """
        if not re.match(r'^(?:GSE|E-MTAB-|EGAD|PRJEB|PRJNA|HRA)', name):
            raise ValueError(f"Collection name '{name}' does not start with 'GSE', 'E-MTAB-', 'EGAD', 'PRJEB', 'PRJNA' or 'HRA'")
        return name

    @field_validator("collections", mode="after")
    @classmethod
    def validate_dataset_collections(cls, collections: List['IrodsCollection'], info: ValidationInfo) -> List['IrodsCollection']:
        """
        Check that dataset collection contains only expected sub-collections: 'metadata', 'raw_data', 'processed_data', 'analysis_results'
        """
        for collection in collections:
            if not re.match(r'^(?:SRS|GSM|ERS)', collection.name):
                logging.warning(f"Collection name '{collection.name}' does not start with 'SRS', 'GSM' or 'ERS'")
        return collections

    @field_validator("data_objects", mode="after")
    @classmethod
    def validate_dataset_data_objects(cls, data_objects: List[str], info: ValidationInfo) -> List[str]:
        """
        Check that dataset collection does not contain any data objects
        """
        series = info.data.get('name')
        prefix = re.match(r'^(?P<prefix>GSE|E-MTAB-)\d+$', series).group("prefix")
        actual_files = set(data_objects)
        expected_files = {
            template.substitute(series=series) 
            for template in cls._expected_files.get("other") | cls._expected_files.get(prefix, set())
        }
        
        # check if all expected files are present
        for file in actual_files:
            for pattern in expected_files:
                if re.fullmatch(pattern, file):
                    expected_files.remove(pattern)
                    break
        
        # log any missing files
        if expected_files:
            logging.warning(f"Dataset collection {info.data.get('path')} is missing expected files: {expected_files}")
        return data_objects


def get_collections_recursive(collection, expected_data_objects=None, expected_collections=None):
    """
    Recursively get collections and data objects from an iRODS collection.
    """
    expected_data_objects = expected_data_objects if expected_data_objects is not None else []
    expected_collections = expected_collections if expected_collections is not None else []

    metadata = defaultdict(list)
    for meta in collection.metadata.items():
        metadata[meta.name].append(meta.value)
    
    collections = [get_collections_recursive(sub_coll) for sub_coll in collection.subcollections]
    data_objects = [data_obj.name for data_obj in collection.data_objects]

    return IrodsCollection(
        name=collection.name,
        path=collection.path,
        create_time=collection.create_time,
        modify_time=collection.modify_time,
        metadata=metadata,
        collections=collections,
        data_objects=data_objects,
        expected_files=set(expected_data_objects),
        expected_collections=set(expected_collections)
    )


def main() -> None:
    # Get iRODS environment file from environment variable
    env_file = os.environ['IRODS_ENVIRONMENT_FILE']

    # Connect to iRODS
    with iRODSSession(irods_env_file=env_file) as session:
        # Get a collection
        collection = session.collections.get('/archive/cellgeni/datasets/GSE120199')

    expected_files = ['.*.accessions.tsv', '.*.ena1.tsv', '.*family.soft', '.*.parsed.tsv', '.*.run.list', '.*.sample.list', '.*.sample_x_run.tsv', '.*solo_qc.*tsv', '.*.urls.list']
    expected_collections = [".*output2"]
    collection = get_collections_recursive(collection, expected_files, expected_collections)

    print(collection)

if __name__ == "__main__":
    main()