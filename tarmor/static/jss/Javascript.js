//EXPORT EQUIPMENT SEARCH TO EXCEL
function exportTableToExcel(tableID, filename = 'Equipment.xlsx') {
    var table = document.getElementById(tableID);
    var wb = XLSX.utils.table_to_book(table, {sheet: "Equipment"});
    XLSX.writeFile(wb, filename);
}

//SELECT DROPDOWN LIST FOR EQ TYPE FROM ASSET TYPE
document.getElementById('id_Asset_Type').addEventListener('change', function() {
    let assetType = this.value;
        fetch(`/ajax/load-equipment-types/?asset_id=${assetType}`)
        .then(response => response.json())
        .then(data => {
            let eqSelect = document.getElementById('id_Equipment_Type');
            eqSelect.innerHTML = '<option value="">Select Type</option>'; 
            data.forEach(item => {
                let option = document.createElement('option');
                option.value = item.Equipment_Type;
                option.text = item.Equipment_Type;
                eqSelect.add(option);
            });
        });
});