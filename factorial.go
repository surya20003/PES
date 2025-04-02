package main

// fmt package provides the function to print anything
import "fmt"

func factorial(number int64) int64 {

   // if the number has reached 1 then we have to
   // return 1 as 1 is the minimum value we have to multiply with
   if number == 1 {
      return 1
   }

   // multiplying with the current number and calling the function
   // for 1 lesser number
   factorialOfNumber := number * factorial(number-1)
   
   // return the factorial of the current number
   return factorialOfNumber
}
func main() {

   // declaring the integer number using the var keyword
   // whose factorial we have to find
   var number int64
   
   // initializing the variable whose factorial we want to find
   number = 5
   
   // calling the factorial() function and printing the factorial
   fmt.Println("The factorial of", number, "is", factorial(number))
   fmt.Println("(Finding the factorial in a recursive manner.)")
}

