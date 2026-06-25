SELECT
    Patient_Id,
    Primary_Treatment,
    Follow_Up_Required,
    Follow_Up_Completed
FROM Patients
WHERE
    Follow_Up_Required = 'Y'
    AND
    Follow_Up_Completed = 'N';