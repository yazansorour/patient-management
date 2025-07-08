# Copyright (c) 2024, wowit and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
import mimetypes
import xml.etree.ElementTree as ET
import numpy as np
import os
import requests
import uuid
from pydicom.uid import generate_uid
# import json
# import base64
from frappe import _
# import httplib2
from pdf2image import convert_from_path, pdfinfo_from_path
# from PIL import Image
import pydicom
from pydicom.dataset import FileDataset
import pydicom.encaps
# import io
# import shutil
# from flask import Flask
import requests

class PDFToDicom(Document):
	# app = Flask(__name__)
	# Image.MAX_IMAGE_PIXELS = None
	# DICOM_FOLDER = "./dicom_files"
	# UPLOAD_FOLDER = "./uploads"
	# ORTHANC_URL = "http://localhost:8042/instances"
	# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
	# os.makedirs(DICOM_FOLDER, exist_ok=True)
	# # app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

	# try:
	# 	Resampling = Image.Resampling
	# except AttributeError:
	# 	Resampling = Image

	def after_insert(self):
        # Perform PDF-to-DICOM conversion after saving the document
		if not self.file:
			frappe.throw("No file attached. Please attach a file.")

        # Retrieve the File document linked to the attachment
		file_doc = frappe.get_doc("File", {"file_url": self.file})
		file_path = (
			frappe.get_site_path("private", "files", file_doc.file_name)
			if file_doc.is_private
			else frappe.get_site_path("public", "files", file_doc.file_name)
        )

		if not os.path.exists(file_path):
			frappe.throw(f"File not found: {file_path}")

        # Determine the file type
		mime_type, _ = mimetypes.guess_type(file_path)

		if mime_type == "application/pdf":
			# if file_path.startswith("."):
			# 	file_path = "/home/frappe/frappe-bench/sites" + file_path[1:]
			# uploaded_files = []
			# uploaded_files.append(file_path)
			# dicom_files = []
			
			# for pdf_path in uploaded_files:
			# 	frappe.msgprint(f"0")
			# 	images = self.pdf_to_images(pdf_path)
			# 	study_uid = pydicom.uid.generate_uid()
			# 	series_uid = pydicom.uid.generate_uid()

			# 	for instance_number, image in enumerate(images, start=1):  # Maintain order with instance_number
			# 		dicom_file = self.image_to_dicom(
			# 			image, self.DICOM_FOLDER, study_uid, series_uid, instance_number
			# 		)
			# 		if dicom_file:
			# 			dicom_files.append(dicom_file)

			# # Upload DICOM files to Orthanc
			# for dicom_file in dicom_files:
			# 	self.send_to_orthanc(dicom_file)

			# shutil.rmtree(self.UPLOAD_FOLDER)
			self.pdf_to_dicom(file_path)
			frappe.msgprint(f"message: Conversion and upload to Orthanc successful \n dicom_files ")
			#frappe.msgprint("Attached file is a PDF. Proceeding with PDF-to-DICOM conversion.")
			# self.convert_pdf_to_dicom(file_path)
			# self.convert_pdf_to_dicom()
		# elif mime_type == "application/xml":
		# 	self.convert_ecg_xml_to_dicom(file_path)
		# elif mime_type == "application/dicom":
		# 	#self.fordicomfile(file_path)
		# 	self.upload_file(file_path)
		else:
			frappe.throw(f"Unsupported file type: {mime_type}")

	def pdf_to_dicom(self,pdf_path):
		

		url = "http://127.0.0.1:8050"

		payload = {
			'patient_name': self.patientname,
			'patient_id': self.patient,
			'birth_date': self.bod,
			'accession_no': self.accession_number,
			'study_date': datetime.now().strftime("%H%M%S"),
			"pdf_path": pdf_path,
			"docname": self.name,
		}
		
		files=[
		('file',(os.path.basename(pdf_path),open(pdf_path,'rb'),'application/pdf'))
		]

		headers = {}

		response = requests.request("POST", url, headers=headers, data=payload, files=files)

		frappe.msgprint(f"{response.text}")

	# def pdf_to_images(self,pdf_path):
	# 	"""Convert a PDF file to images and return them as in-memory PIL Image objects."""
	# 	try:
	# 		frappe.msgprint(f"1{pdf_path}")
	# 		info = pdfinfo_from_path(pdf_path)
	# 		frappe.msgprint(f"5")
	# 		total_pages = info.get("Pages", 0)
	# 		images = []
	# 		for page_number in range(1, total_pages + 1):
	# 			frappe.msgprint(f"3")
	# 			page_images = convert_from_path(pdf_path, dpi=300, first_page=page_number, last_page=page_number, timeout=50000)
	# 			frappe.msgprint(f"1{page_images}")
	# 			for img in page_images:
	# 				if img.getbbox() is None:  # Skip blank pages
	# 					continue
	# 				img = self.resize_image_if_needed(img)
	# 				images.append(img)
	# 		return images
	# 	except Exception as e:
	# 		print(f"Error in pdf_to_images: {e}")
	# 		return []
		
	# def resize_image_if_needed(self,image, max_width=2048, max_height=2048):
	# 	"""Resize image if it exceeds the specified max dimensions while maintaining aspect ratio."""
	# 	width, height = image.size
	# 	if width > max_width or height > max_height:
	# 		img_ratio = width / height
	# 		max_ratio = max_width / max_height
	# 		if img_ratio > max_ratio:
	# 			new_width = max_width
	# 			new_height = int(max_width / img_ratio)
	# 		else:
	# 			new_width = int(max_height * img_ratio)
	# 			new_height = max_height
	# 		return image.resize((new_width, new_height), self.Resampling.LANCZOS)
	# 	return image
	
	# def image_to_dicom(
	# 	self,image, output_folder, study_uid, series_uid, instance_number
	# ):
	# 	"""Convert an in-memory image (PIL Image) to a DICOM file using JPEG Lossless Compression."""
	# 	try:
	# 		dicom_filename = os.path.join(output_folder, f"{uuid.uuid4().hex}.dcm")

	# 		# Create basic DICOM metadata
	# 		file_meta = pydicom.dataset.FileMetaDataset()
	# 		file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
	# 		file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
	# 		file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.4.50"  # JPEG Baseline

	# 		# Create the dataset
	# 		ds = FileDataset(dicom_filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
	# 		ds.PatientName = self.patientname
	# 		ds.PatientID = self.patient
	# 		ds.PatientBirthDate = self.dob
	# 		ds.AccessionNumber = self.accession_number
	# 		ds.StudyInstanceUID = study_uid  # Use the provided StudyInstanceUID
	# 		ds.SeriesInstanceUID = series_uid  # Use the provided SeriesInstanceUID
	# 		ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
	# 		ds.Modality = self.modality_code # "OT"  # Other
	# 		ds.StudyDate = datetime.now().strftime("%Y%m%d")  # Set the provided Study Date
	# 		ds.StudyTime = datetime.now().strftime("%H%M%S")

	# 		# Convert the in-memory image to JPEG Lossless-compressed binary data
	# 		if image.mode != "RGB":
	# 			image = image.convert("RGB")  # Ensure image is in RGB mode

	# 		buffer = io.BytesIO()
	# 		image.save(buffer, format="JPEG", quality=95)  # Use quality=95 for JPEG Baseline
	# 		buffer.seek(0)
	# 		compressed_pixel_data = buffer.read()

	# 		# Encapsulate the pixel data (required for JPEG Lossless)
	# 		ds.PixelData = pydicom.encaps.encapsulate([compressed_pixel_data])

	# 		# Set DICOM attributes for compressed image
	# 		width, height = image.size
	# 		ds.Rows = height
	# 		ds.Columns = width
	# 		ds.SamplesPerPixel = 3  # RGB has 3 samples per pixel
	# 		ds.PhotometricInterpretation = "RGB"  # Set to RGB for JPEG Lossless
	# 		ds.BitsAllocated = 8  # 8 bits per channel
	# 		ds.BitsStored = 8
	# 		ds.HighBit = 7
	# 		ds.PixelRepresentation = 0  # Unsigned integer
	# 		ds.PlanarConfiguration = 0  # Pixel data is stored in RGBRGB order

	# 		# Add essential metadata required by viewers
	# 		ds.ImagesInAcquisition = "1"
	# 		ds.ImageType = ["DERIVED", "PRIMARY", "AXIAL"]
	# 		ds.InstanceNumber = instance_number  # Maintain the order of images
	# 		ds.PositionReferenceIndicator = "ORIGIN"
	# 		ds.PixelAspectRatio = [1, 1]

	# 		# Save the DICOM file
	# 		ds.save_as(dicom_filename)
	# 		print(f"Debug: DICOM file saved at {dicom_filename}")
	# 		return dicom_filename
	# 	except Exception as e:
	# 		print(f"Error in image_to_dicom: {e}")
	# 		return None
		
	# def send_to_orthanc(self,dicom_file):
		# """Send a DICOM file to the Orthanc server."""
		# try:
		# 	with open(dicom_file, "rb") as file:
		# 		response = requests.post(self.ORTHANC_URL, files={"file": file})
		# 		if response.status_code == 200 or response.status_code == 204:
		# 			print(f"Successfully uploaded {dicom_file} to Orthanc.")
		# 			return True
		# 		else:
		# 			print(f"Failed to upload {dicom_file} to Orthanc. Response: {response.text}")
		# 			return False
		# except Exception as e:
		# 	print(f"Error sending to Orthanc: {e}")
		# 	return False
