/**
 * Filters tables from the response based on the provided table name, key, and code.
 *
 * @param {Object} response - The response object containing the tables.
 * @param {string} tableName - The name of the table to filter.
 * @param {string} code - The code to filter the entries by.
 * @returns {Object|null} - The parsed error data if found, otherwise null.
 */
export const filterTables = (response, tableName, code) => {
    try {
        // Ensure the response and necessary properties exist
        if (!response?.result?.tables[0]) {
            throw new Error("Invalid response format");
        }

        const tables = response.result.tables[0];
        const table = tables[tableName];

        // Ensure the table exists
        if (!table) {
            throw new Error(`Table ${tableName} not found`);
        }

        const results = table.filter((entry) => entry.code === code);

        // Ensure there are results and the key exists in the results
        if (results.length > 0 && results[0]) {
            if(typeof(results[0]["error-data"]) === "string"){
                let errorData = JSON.parse(results[0]["error-data"]);
                return errorData
            }
            else{
                let errorData = []
                results.forEach((type) => {
                    errorData.push(type["error-data"]);
                })
                return errorData;
            }
            
        }
        return null;
    } catch (error) {
        console.error("Error filtering tables:", error);
        return null;
    }
};

/**
 * Filters the Data Summary info into table structure to be displayed 
 * 
 * @param {Object} data - The table data.
 * @returns {Object} An object containing column headers and rows.
 * @returns {Array<string>} return.columnHeaders - An array of column headers.
 * @returns {Array<Object>} return.rows - An array of row objects.
 */

export const createHeadersAndRows = (data) => {
    const columnHeaders = ["node", ...Object.keys(data[Object.keys(data)[0]])];
    const rows = Object.keys(data).map((node) => {
        const row = { node };
        Object.keys(data[node]).forEach((key) => {
            row[key] = data[node][key] !== null ? data[node][key] : 'null';
        });
        return row;
    });
    return { columnHeaders, rows };
};

/**
 * Processes table data by filtering the tables and creating headers and rows.
 * 
 * @param {Object} response - The response object containing table data.
 * @param {string} tableName - The name of the table to filter.
 * @param {string} code - The code to filter the table entries by.
 * @returns {Object} An object containing column headers and rows.
 * @returns {Array<string>} return.columnHeaders - An array of column headers.
 * @returns {Array<Object>} return.rows - An array of row objects.
 */
export const processTableData = (response, tableName, code) => {
    const data = filterTables(response, tableName, code);
    const { columnHeaders, rows } = createHeadersAndRows(data);
    return { columnHeaders, rows }
}