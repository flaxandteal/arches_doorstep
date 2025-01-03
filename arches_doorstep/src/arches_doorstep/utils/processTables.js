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