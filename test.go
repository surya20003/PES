
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	"github.com/xuri/excelize/v2"
)

// Database Config
const (
	host     = "localhost"
	port     = 5432
	user     = "postgres"
	password = "suryakk07"
	dbname   = "hsn-db"
)

func readExcel() {
	// Open the Excel file
	f, err := excelize.OpenFile("HSN_SAC.xlsx")
	if err != nil {
		log.Fatal("Error opening Excel file:", err)
	}
	defer f.Close()

	// Read HSN Master Sheet
	rows, err := f.GetRows("hsn_mstr")
	if err != nil {
		log.Fatal("Error reading HSN sheet:", err)
	}
	fmt.Println("HSN Master Data:")
	for _, row := range rows {
		fmt.Println(row)
	}

	// Read SAC Master Sheet
	rows, err = f.GetRows("sac_mstr")
	if err != nil {
		log.Fatal("Error reading SAC sheet:", err)
	}
	fmt.Println("SAC Master Data:")
	for _, row := range rows {
		fmt.Println(row)
	}
}

func main() {
	// Read Excel data
	readExcel()

	// Connect to PostgreSQL
	db, err := sql.Open("postgres", fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname))
	if err != nil {
		log.Fatal("Database connection error:", err)
	}
	defer db.Close()

	// Setup API server
	r := gin.Default()

	// API Route
	r.GET("/hsn_sac", func(c *gin.Context) {
		query := `
			SELECT h.hsn_code, h.description AS hsn_desc, 
				   COALESCE(s.sac_code, '') AS sac_code, 
				   COALESCE(s.description, '') AS sac_desc
			FROM hsn_mstr h
			LEFT JOIN sac_mstr s ON h.hsn_code = s.hsn_code;
		`
		rows, err := db.Query(query)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer rows.Close()

		var results []map[string]string
		for rows.Next() {
			var hsnCode, hsnDesc, sacCode, sacDesc string
			err = rows.Scan(&hsnCode, &hsnDesc, &sacCode, &sacDesc)
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
				return
			}
			results = append(results, map[string]string{
				"hsn_code": hsnCode,
				"hsn_desc": hsnDesc,
				"sac_code": sacCode,
				"sac_desc": sacDesc,
			})
		}
		c.JSON(http.StatusOK, results)
	})

	// Start API Server
	fmt.Println("Server is running on port 8080...")
	r.Run(":8080")
}
