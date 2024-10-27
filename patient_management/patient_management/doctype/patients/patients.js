//English 1
frappe.ui.form.on('Patients', {
    refresh(frm){
        if(frm.doc.name.startsWith('new')){
            var now = new Date()
            console.log(String(now.getFullYear()) + String(now.getMonth() + 1).padStart(2, '0') +String(now.getDay()).padStart(2, '0') + String(now.getHours()).padStart(2, '0') + String(now.getMinutes()).padStart(2, '0') + String(now.getSeconds()).padStart(2, '0'))
            var created_at = String(now.getFullYear()) + String(now.getMonth() + 1).padStart(2, '0') +String(now.getDay()).padStart(2, '0') + String(now.getHours()).padStart(2, '0') + String(now.getMinutes()).padStart(2, '0') + String(now.getSeconds()).padStart(2, '0')
            console.log(created_at)
            frm.set_value({
                created_at: created_at,
                updated_at: created_at
            })
            // console.log(frm.doc.created_at)
            // console.log(frm.doc.updated_at)
    }
    
      frm.add_custom_button(__("Get Patient Assist"), function() {
          frappe.call({
            	    "method": "ai_intergration.ai_intergration.api.getAIResponse",
            	args:{
            	    mctName:"179gdl4mpu",
            	    docName:frm.doc.name,
            	},
            	callback:function(r){
            	   frm.set_value("ai_report", r.message);
            	}
            	});
        }).addClass("btn-primary");    
    
    },
    
    validate(frm){
        if(frm.doc.name.startsWith('new') == false) {
            var updated_at = frm.doc.modified
            var update_date = updated_at.split(" ")[0].split("-")
            var update_time = updated_at.split(" ")[1].split(".")[0].split(":")
            
            updated_at = update_date[0] + update_date[1] + update_date[2] + update_time[0] + update_time[1] + update_time[2]
            // frm.doc.created_at = created_at
            // frm.doc.updated_at = updated_at
            frm.set_value({
                updated_at: updated_at
            })
        }
        if(frm.doc.name.startsWith('new')){
            frappe.call({
                    method: 'casting.casting.packs-api.sendHL7Message',
                    args: {
                        docType: 'Patients',
                        docName:frm.doc,
                        action:'Create'
                    },
                    // disable the button until the request is completed
                    // freeze the screen until the request is completed
                    callback: (r) => {
                        console.log("Created")
                        console.log(r.message)
                        
                    },
                    error: (r) => {
                        console.log(r)
                    }
                })
        }
        else{
             frappe.call({
                    method: 'casting.casting.packs-api.sendHL7Message',
                    args: {
                        docType: 'Patients',
                        docName:JSON.stringify(frm.doc),
                        action:'Update'
                    },
                    // disable the button until the request is completed
                    // freeze the screen until the request is completed
                    callback: (r) => {
                        console.log("Updated")
                    },
                    error: (r) => {
                        console.log(r)
                    }
                })
        }
        frm.doc.full_name = frm.doc.first_name + " " + frm.doc.second_name + " " + frm.doc.third_name + " " + frm.doc.last_name;
        
      var dob = new Date(frm.doc.dob);
      var now = new Date();
      var age_now = now.getFullYear() - dob.getFullYear();
        // use frm.set_value to set value of a field
      frm.set_value('age',age_now);

        
    },
	first_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'english_name': frm.doc.first_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.ara_1st_name = res[0].arabic_name;
        	        refresh_field('ara_1st_name');
        	    }
	        });
	}
})

//English 2
frappe.ui.form.on('Patients', {
	second_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'english_name': frm.doc.second_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.ara_2nd_name = res[0].arabic_name;
        	        refresh_field('ara_2nd_name');
        	    }
	        });
	}
})

//English 3
frappe.ui.form.on('Patients', {
	third_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'english_name': frm.doc.third_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.ara_3rd_name = res[0].arabic_name;
        	        refresh_field('ara_3rd_name');
        	    }
	        });
	}
})

//English 4
frappe.ui.form.on('Patients', {
	last_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'english_name': frm.doc.last_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.ara_last_name = res[0].arabic_name;
        	        refresh_field('ara_last_name');
        	    }
	        });
	}
})

//Arabic 1
frappe.ui.form.on('Patients', {
	ara_1st_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'arabic_name': frm.doc.ara_1st_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.first_name = res[0].english_name;
        	        refresh_field('first_name');
        	    }
	        });
	}
})

//Arabic 2
frappe.ui.form.on('Patients', {
	ara_2nd_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'arabic_name': frm.doc.ara_2nd_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.second_name = res[0].english_name;
        	        refresh_field('second_name');
        	    }
	        });
	}
})

//Arabic 3
frappe.ui.form.on('Patients', {
	ara_3rd_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'arabic_name': frm.doc.ara_3rd_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.third_name = res[0].english_name;
        	        refresh_field('third_name');
        	    }
	        });
	}
})

//Arabic 4
frappe.ui.form.on('Patients', {
	ara_last_name(frm) {
	    frappe.db.get_list('Translated Name', { filters: { 'arabic_name': frm.doc.ara_last_name, },
	        fields: ['english_name', 'arabic_name']}).then(res => {
	            if(res.length > 0){
        	        frm.doc.last_name = res[0].english_name;
        	        refresh_field('last_name');
        	    }
	        });
	}
})
