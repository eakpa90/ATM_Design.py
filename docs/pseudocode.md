FUNCTION ProcessATMTransaction():
    
    // --- FAILURE SCENARIO 1: Card Cannot Be Read ---
    read_attempts = 0
    card = NULL
    
    WHILE read_attempts < 2 AND card == NULL:
        card = Hardware.ReadCardSlot()
        IF card == NULL:
            read_attempts = read_attempts + 1
            UI.DisplayMessage("Card read error. Please wipe chip and try again.")
            Wait(3_SECONDS)
            
    IF card == NULL OR card.IsExpired() OR card.IsBlacklisted():
        Hardware.EjectCard()
        DISPLAY "Card unreadable or invalid. Session terminated."
        RETURN TERMINATE_SESSION


    // --- FAILURE SCENARIO 2: Incorrect PIN ---
    attempts = 0
    authenticated = FALSE
    
    WHILE attempts < 3 AND NOT authenticated:
        pin_input = UI.PromptUserForPIN()
        
        IF card.VerifyPIN(pin_input):
            authenticated = TRUE
        ELSE:
            attempts = attempts + 1
            remaining = 3 - attempts
            IF remaining > 0:
                UI.DisplayMessage("Incorrect PIN. " + remaining + " tries remaining.")
            
    IF NOT authenticated:
        Hardware.RetainCard() // Security interlock: swallow card to prevent theft
        Security.LogAlert("Card retained due to max PIN failures.")
        UI.DisplayMessage("Incorrect PIN entered 3 times. Card retained for security.")
        RETURN TERMINATE_SESSION


    // --- FAILURE SCENARIO 3 & 4: Amount Validation & ATM Cash Inventory ---
    valid_amount_entered = FALSE
    
    WHILE NOT valid_amount_entered:
        amount = UI.PromptEnterAmount()
        
        // Check ATM physical inventory/denominations first
        IF NOT Hardware.CanDispenseDenominations(amount):
            UI.DisplayMessage("ATM cannot dispense this exact amount with available bills. Try a multiple of $20.")
            CONTINUE // Loop back for a new amount
            
        IF amount > Account.GetBalance():
            UI.DisplayMessage("Insufficient funds. Your balance is $" + Account.GetBalance())
            CHOICE = UI.PromptUser("Would you like to try a different amount?", ["Retry", "Cancel"])
            IF CHOICE == "Cancel":
                Hardware.EjectCard()
                RETURN TERMINATE_SESSION
            ELSE:
                CONTINUE
                
        valid_amount_entered = TRUE


    // --- FAILURE SCENARIO 5: Transaction Failure Mid-Execution (Atomicity & Rollback) ---
    server_status = BankServer.RequestAuthorization(Account.ID, amount)
    
    IF server_status == NETWORK_TIMEOUT:
        UI.DisplayMessage("Connection error with bank server. Please try another machine.")
        Hardware.EjectCard()
        RETURN TERMINATE_SESSION
        
    // Server approved, now attempt physical cash delivery
    dispense_success = Hardware.DispenseCash(amount)
    
    IF NOT dispense_success:
        // CRITICAL: Mechanical Jam occurred *after* server approval
        BankServer.RollbackAndRefund(Account.ID, amount) // Protect user's money!
        Hardware.TriggerMaintenanceFlag()
        UI.DisplayMessage("Mechanical error occurred. Transaction cancelled. No funds deducted.")
        Hardware.EjectCard()
        RETURN TERMINATE_SESSION

    // Successful wrap up
    BankServer.CommitTransaction(Account.ID, amount)
    Hardware.EjectCard()
    UI.DisplayMessage("Please take your cash and receipt. Thank you!")
    RETURN SUCCESS