# Assesment Calendar App

## Interview

### Interview and Transcript

Please see attached transcript or see the below notes.

![Interview Transcript](InterviewWithMichael.md)

### Interview Notes

#### Current System

Teachers currently have to manually enter assessment data into multiple places like ACS, Schoolbox, and an Excel calendar. This means there’s a lot of double handling and inconsistency between what’s written in each system. Different teachers use different naming styles and formats, so sometimes course titles or task names don’t match. Students also have to dig through clunky portals or shared spreadsheets to see their due dates, and they aren’t notified when things change. Overall, the system is time consuming and hard to use for both teachers and students.

#### Desired System

A system that makes entering and viewing assessments simpler for everyone. Teachers should be able to easily add assessments using drop-downs or predictive text so that everything is consistent. It should also show if there are any clashes with other subjects before finalising dates. Students should then be able to access a personalised calendar that only shows their subjects and tasks, ideally in a clean and easy-to-read layout. In the future, it could even notify students when assessment details are updated.

## Preplanning

### What problems will I solve

#### Teacher Data Entry

I will be improving on the current Excel data entry page for Teachers, this will hopefully make a more clear and streamlined process. My version of the Excel will create clear seperate sections for year 11 and 12 along with addign a section for each piece of key information, instead of the current system where there is only a single input field per day. Along with this inorder to reduce assesment clashes Michale has suggested limiting the number of assesments possibly due on a day, which i have included by ony providing three input fields per day.

#### Student Assessment Calendar - Ease of use and Accuracy

Currently the assesment calendar is just an excel sheet, spread out to students via schoolbox, where they then have to sort through and find only information relevant to them. I plan to fix this by creating a user interface which props the user to upload the same excel sheet from school box, then promps them for their name, which checks that against a look up table, hence softing the uploaded sheet for only relevant information, which it then displays.

#### Student Assesment Calendar - Data Standardisation and Accessibility

Provide consistant naming for assesments and a standard layout for the data.

### If I have more time

Although unlikely since the small length of this term, creating a more indepth teacher side that works with a server to check for overlapping assesment dates, would be my dream if i have more time goal.

## Development

### Prototype 1: Extract Data and display Calendar

#### Video of Functionality

[![First Prototype](https://img.youtube.com/vi/0XVEEeXoc/0.jpg)](https://www.youtube.com/watch?v=i_0XVEEeXoc)

#### Issues

One of the main issues in this section, came when I was testing what happened when the excel sheet has been shifted over a column or two since it occured to me that that might be a common error if for anyreason a note or something similar had to be put to the side of the data. I solved this with my "find_header_row" function in extractdata.py, which checks for the header row within a range of other rows. 

Another issue was the excel since I had merged cells to make it more astetically appeasing didn't recognise those cells with the following the first one as having that value, so I created a "fill_down" that filled out the values below the first one to reflect it until it encountered the next full one.

### Prototype 2: Display Class Color

#### Video of Functionality

[![2nd Prototype](https://img.youtube.com/vi/VriVXap3Zhc/0.jpg)](https://www.youtube.com/watch?v=i_VriVXap3Zhc)

#### Issues

An issue which I ended up solving, was the issue of having multiple assesments from multiple diffirent classes on the same day. My original plan was to have it merge/blend the colors but this involved first seperating the hexcodes into rgb then finding the average value and turning that back into hexcodes, which I attempted to do for a while but eventually ended up giving up and resolving this issue by just having it check for what subject has the highest weighted assesment.

### Prototype 3: Side bar view

#### Video of Functionality

[![3rd Prototype](https://img.youtube.com/vi/dP_SjNt3R-4/0.jpg)](https://www.youtube.com/watch?v=i_dP_SjNt3R-4)

#### Issues



### Prototype 4: Import data

#### Video of Functionality

[![4th Prototype](https://img.youtube.com/vi/HmCbDyk119M/0.jpg)](https://www.youtube.com/watch?v=i_HmCbDyk119M)

#### Issues

Although this was an easy fix it made it much more usable and readable. When I would scan for classes it would include all occurences of them in the excel sheet, which would allow the user to select multiple of the same classes. I fixed this by checking if they were unique. 

## Reflection

### Feedback From Michael

Unfortionatly I was unable to get a direct quote from michael as I showed it to him before the end of class. But he said something along the lines of, "This is good... I like what you've done here... How does this work and could it be improved". So overall he liked the final version and I believe it solved some of the problems that were brought up in the interview.

### What Issues did I Encounter

The main over arching issue was length of the term and how I managed the time. This resulting in me having to do the majority of this documentation on the day of submission instead of my usual time frame, of only polishing the documentation on the final day. Along with documentation these time constrants also effected the actual development of the app, with me completing the majority of it over this last week.

### What have I Learnt

As I said above with this reduced time frame compared to the usual IT assignemnt I struggled to complete most of my plans in time only managing to scrape it in last minute. This lead me to learn that in these short terms where we only have a few weeks to do everything, it is very important to begin early and continue consistently until it is finished.
