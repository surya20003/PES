package main


import (

    "database/sql"

    "fmt"

    "log"


    _ "github.com/mattn/go-sqlite3" // Import the SQLite driver

)


// HSNData struct to hold HSN code information

type HSNData struct {

    Description string

    GSTRate     float64

}


// Function to connect to the database and retrieve HSN data

func GetHSNDataFromDB(db *sql.DB, hsnCode string) (HSNData, error) {

    var data HSNData

    query := "SELECT description, gst_rate FROM hsn_codes WHERE hsn_code = ?"

    err := db.QueryRow(query, hsnCode).Scan(&data.Description, &data.GSTRate)

    if err != nil {

        if err == sql.ErrNoRows {

            return HSNData{}, fmt.Errorf("HSN Code %s not found", hsnCode)

        }

        return HSNData{}, fmt.Errorf("failed to query database: %w", err)

    }

    return data, nil

}


func main() {

    // Open the SQLite database (or create it if it doesn't exist)

    db, err := sql.Open("sqlite3", "hsn_data.db")

    if err != nil {

        log.Fatal(err)

    }

    defer db.Close()


    // Create the table if it doesn't exist

    _, err = db.Exec(`

        CREATE TABLE IF NOT EXISTS hsn_codes (

            hsn_code TEXT PRIMARY KEY,

            description TEXT,

            gst_rate REAL

        )

    `)

    if err != nil {

        log.Fatal(err)

    }


    // Insert some sample data (you would likely do this from a file or other source)

    _, err = db.Exec(`

        INSERT OR IGNORE INTO hsn_codes (hsn_code, description, gst_rate) VALUES

            ('09021000', 'Green tea, not fermented', 0.05),

            ('19053100', 'Sweet biscuits', 0.18),

            ('85171211', 'Mobile phones with push-button keypad', 0.12),

            ('94032010', 'Metal furniture of a kind used in offices, of steel', 0.18);

    `)

    if err != nil {

        log.Fatal(err)

    }


    hsn := "19053100"

    data, err := GetHSNDataFromDB(db, hsn)

    if err != nil {

        fmt.Println(err)

    } else {

        fmt.Printf("HSN Code: %s\n", hsn)

        fmt.Printf("Description: %s\n", data.Description)

        fmt.Printf("GST Rate: %.2f%%\n", data.GSTRate*100)

    }


    notFoundHSN := "99999999"

    _, err = GetHSNDataFromDB(db, notFoundHSN)

    if err != nil {

        fmt.Println(err)

    }

}
