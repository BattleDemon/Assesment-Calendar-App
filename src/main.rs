

slint::slint!{
    export component HelloWorld {
        Text {
            text: "hello world";
            color: green;
        }
    }
}

slint::include_modules!();
fn main() {
    HelloWorld::new().unwrap().run().unwrap();
}