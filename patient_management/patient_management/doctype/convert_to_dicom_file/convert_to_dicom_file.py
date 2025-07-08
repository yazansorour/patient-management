# Copyright (c) 2024, wowit and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
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
import json
import base64
from frappe import _
import httplib2

class ConvertToDicomFile(Document):
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
			#frappe.msgprint("Attached file is a PDF. Proceeding with PDF-to-DICOM conversion.")
			# self.convert_pdf_to_dicom(file_path)
			self.convert_pdf_to_dicom()
		elif mime_type == "application/xml":
			#frappe.msgprint("Attached file is an XML. Proceeding with ECG XML-to-DICOM conversion.")
			self.convert_ecg_xml_to_dicom(file_path)
		elif mime_type == "application/dicom":
			#frappe.msgprint("Attached file is an XML. Proceeding with ECG XML-to-DICOM conversion.")
			#self.fordicomfile(file_path)
			frappe.msgprint(f"start Upload3223:")
			self.upload_file(file_path)
		else:
			frappe.throw(f"Unsupported file type: {mime_type}")
		

	def convert_pdf_to_dicom(self):
        # Ensure there's a file attached
		if not self.file:
			frappe.throw("Please attach a PDF file to convert.")

        # Get the file path
		file_doc = frappe.get_doc("File", {"file_url": self.file})
		if file_doc.is_private:
			file_path = frappe.get_site_path("private", "files", file_doc.file_name)
		else:
			file_path = frappe.get_site_path("public", "files", file_doc.file_name)
    

        
		if not os.path.exists(file_path):
			frappe.throw(f"File not found: {file_path}")

        # Read the PDF as binary
		with open(file_path, "rb") as f:
			pdf_data = f.read()

        # Create DICOM file meta information
		file_meta = FileMetaDataset()
		file_meta.MediaStorageSOPClassUID = generate_uid()
		file_meta.MediaStorageSOPInstanceUID = generate_uid()
		file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        # Create the DICOM dataset
		ds = Dataset()
		ds.PatientName = self.patientname
		ds.PatientID = self.patient
		ds.Modality = self.modality or "DOC"
		ds.ContentType = "application/pdf"
		ds.EncapsulatedDocument = pdf_data
		root = "1.3.46.670589.11.0.1"  # Example root prefix for your system/organization
		unique_component = uuid.uuid4().int  # Convert UUID to integer
		study_instance_uid = f"{root}.{unique_component}"

		# Ensure it's DICOM-compliant
		#study_instance_uid = generate_uid(prefix=root)
		ds.StudyInstanceUID = study_instance_uid  # Unique Study Instance UID
		ds.SeriesInstanceUID = str(uuid.uuid4())  # Unique Series Instance UID
		ds.SOPInstanceUID = str(uuid.uuid4())  # 
		ds.AccessionNumber = self.accession_number
        # Save as a DICOM file
		dicom_filename = f"{self.name}.dcm"
		output_path = frappe.get_site_path("public", "files", dicom_filename)
		ds.file_meta = file_meta
		ds.is_implicit_VR = False
		ds.is_little_endian = True
		pydicom.filewriter.write_file(output_path, ds)

        # Attach the DICOM file back to the document
		file_doc = frappe.get_doc({
            "doctype": "File",
            "file_url": f"/files/{dicom_filename}",
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name,
        })
		file_doc.insert()

		self.send_to_orthanc(output_path)

		frappe.msgprint(f"DICOM file generated and attached: {output_path}")

	def fordicomfile(self,file_path):
		file_doc = frappe.get_doc({
            "doctype": "File",
            "file_url": f"/files/{file_path}",
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name,
        })
		file_doc.insert()

		self.send_to_orthanc(file_doc.file_url)

	def convert_ecg_xml_to_dicom(self, file_path):
    # Ensure the file exists
		if not os.path.exists(file_path):
			frappe.throw(f"File not found: {file_path}")

		# Parse the ECG XML
		try:
			import xml.etree.ElementTree as ET
			import numpy as np

			tree = ET.parse(file_path)
			root = tree.getroot()

			# Example: Extract ECG waveform data from the XML
			waveforms = root.find("Waveforms")
			if waveforms is None:
				frappe.throw("No waveforms found in the XML file.")

			waveform_data = []
			sampling_frequency = None
			for waveform in waveforms.findall("Waveform"):
				points = waveform.find("Points").text.split()
				waveform_data.append([float(point) for point in points])
				if sampling_frequency is None:
					sampling_frequency = float(waveform.find("SamplingFrequency").text)

			# Convert waveform data to a NumPy array
			waveform_array = np.array(waveform_data, dtype=np.float32)
		except Exception as e:
			frappe.throw(f"Error parsing ECG XML: {str(e)}")

		# Create DICOM file meta information
		from pydicom.dataset import Dataset, FileMetaDataset
		from pydicom.uid import ExplicitVRLittleEndian, generate_uid
		import pydicom.filewriter

		file_meta = FileMetaDataset()
		file_meta.MediaStorageSOPClassUID = generate_uid() # "1.2.840.10008.5.1.4.1.1.9.1.1"  # ECG Waveform Storage
		file_meta.MediaStorageSOPInstanceUID = generate_uid()
		file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

		# Create the main dataset
		ds = Dataset()
		ds.PatientName = self.patientname
		ds.PatientID = self.patient
		ds.Modality = "ECG"
		ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
		ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
		ds.StudyInstanceUID = generate_uid()
		ds.SeriesInstanceUID = generate_uid()
		ds.InstanceCreationDate = pydicom.valuerep.DA()  # Today's date
		ds.InstanceCreationTime = pydicom.valuerep.TM()  # Current time

		# Add waveform data
		ds.WaveformSequence = []
		waveform_item = Dataset()
		waveform_item.MultiplexGroupTimeOffset = 0
		waveform_item.ChannelSensitivity = 1.0
		waveform_item.SamplingFrequency = sampling_frequency
		waveform_item.WaveformBitsAllocated = 32
		waveform_item.WaveformSampleInterpretation = "SS"  # Signed integer
		waveform_item.WaveformData = waveform_array.tobytes()
		ds.WaveformSequence.append(waveform_item)

		# Save the DICOM file
		dicom_filename = f"{self.name}_ecg.dcm"
		output_path = frappe.get_site_path("public", "files", dicom_filename)
		ds.file_meta = file_meta
		ds.is_implicit_VR = False
		ds.is_little_endian = True
		pydicom.filewriter.write_file(output_path, ds)

		# Attach the DICOM file back to the document
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_url": f"/files/{dicom_filename}",
			"attached_to_doctype": self.doctype,
			"attached_to_name": self.name,
		})
		file_doc.insert()

		frappe.msgprint(f"ECG DICOM file generated and attached: {file_doc.file_url}")

	def send_to_orthanc(self,file):
		url = "http://localhost:8042/instances"
		dicom_file_path = file

		try:

			with open(dicom_file_path, "rb") as file:
				headers = {"Content-Type": "application/dicom"}
				response = requests.post(url, data=file, headers=headers)
			if response.status_code == 200:
				response_data = response.json()
				frappe.msgprint(f"Response: {response_data}")
				#self.createStudy(response_data['ID'])

				frappe.msgprint(f"Response: {response_data['ID']}")
			else:
				frappe.msgprint(f"Error: Failed to upload the DICOM file. Response Code: {response.status_code}")
				frappe.msgprint("Details:", response.text)

		except FileNotFoundError:
			frappe.msgprint(f"response{response.status_code}")
			frappe.msgprint(f"{response.json()}")
		except requests.exceptions.RequestException as e:
			frappe.msgprint(f"An error occurred while making the request: {e}")


	@frappe.whitelist()
	def createStudy(self,instanceID):
		url = 'http://localhost:8042/instances/'+instanceID

		instance_response = requests.get(url = url+"/tags")
		study_response = requests.get(url = url+"/study")
		modAET = requests.get(url = url + "/metadata/RemoteAET")
		modIP = requests.get(url = url + "/metadata/RemoteIP")
		#accession_number
		# Study Instance ID - frappe
		studyFID = ''
		# Get Instance Tags 
		instanceTags = json.loads(instance_response.text)
		study = json.loads(study_response.text)

		# ------- Check if the study coming from query other hospital ------------ #
		#isStudyComingFromQuery = checkIfStudyIsQueried(modAET.text)

		"""
		TODO get modilty AET and ip 
		check if the modilty exist
		if not create new one
		"""

		hospital_id = self.hospitalid
		
		if self.patient != None:
			stuDoc = frappe.new_doc("PACS Study")
			stuDoc.patient_identifier = self.patient
			try:
				stuDoc.study_description = instanceTags['0008,1030']['Value']
				stuDoc.accession_number = instanceTags['0008,0050']['Value']
			except:
				print('Not Found !')
			frappe.msgprint(f'{instanceTags}')
			stuDoc.modality_name = instanceTags['0008,0060']['Value']
			if '0008,0020' in instanceTags:
				stuDoc.study_date = instanceTags['0008,0020']['Value'][0:4] + '-' + instanceTags['0008,0020']['Value'][4:6] + '-' + instanceTags['0008,0020']['Value'][6:8]
			stuDoc.studyinstanceuid = instanceTags['0020,000d']['Value']
			stuDoc.view_imagest = "/viewer?StudyInstanceUIDs={}".format(instanceTags['0020,000d']['Value'])
			stuDoc.study_id = study['ID']
			stuDoc.insert(ignore_permissions=True)
			studyFID = stuDoc.name
			# set patient oid
			curPatient = frappe.get_doc('Patients' , self.patient)
			curPatient.pateint_oid = study['ParentPatient']
			curPatient.save(ignore_permissions=True)
		
		newStudy = frappe.get_doc('PACS Study',studyFID)

		rd = frappe.get_doc('Radiology Order' , self.order)
		rd.studies = newStudy.name
		rd.view_imagest = newStudy.view_imagest
		newStudy.radiology_order = rd.name
		rd.save(ignore_permissions=True)
		newStudy.save(ignore_permissions=True)

	def upload_file(self,dicom):
		frappe.msgprint(f"start Upload3223:")
		try:
			# Read the file as bytes
			with open(dicom, "rb") as file:
				file_bytes = file.read()

			# Convert bytes to base64 string
			base64_string = base64.b64encode(file_bytes).decode("utf-8")
			frappe.msgprint(f"start Upload:")
			# Make Frappe API call
			response = self.uploadDicom(base64_string,self.hospitalid)

			if response.get("exc"):
				frappe.msgprint(f"Upload failed")

		except Exception as e:
			frappe.msgprint(f"File Upload Error")
			

	def uploadDicom(self,file , hospitalID):
		#f = base64.b64decode(file + "==")
		#content = f.read()
		# Open file in binary write mode
		decoded = base64.b64decode(file)
		"""
		f = open("test.dcm", "wb")
		f.write(decoded)
		f.close()
		"""
		hid_bytes = hospitalID.encode('ascii')
		hid = base64.b64encode(hid_bytes)
		h = httplib2.Http()
		headers = {'content-type' : 'application/dicom'} #'Authorization': 'Basic {}'.format(hid.decode('ascii'))}
		resp, content = h.request('http://127.0.0.1:8042/instances', 'POST', 
									body = decoded,
									headers = headers)
		if resp.status == 200:
			frappe.msgprint(f'Upload Successfly:{resp}////{content}')
		else:
			frappe.msgprint(f'not Successfly')