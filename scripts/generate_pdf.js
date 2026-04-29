const puppeteer = require('puppeteer');
const path = require('path');

async function generatePDF() {
    const htmlFile = path.join(__dirname, '../template/company_rule.html');
    const outputPDF = path.join(__dirname, '../template/company_rule.pdf');

    try {
        const browser = await puppeteer.launch({
            headless: 'new'
        });

        const page = await browser.newPage();

        // HTMLファイルを開く
        await page.goto(`file://${htmlFile}`, {
            waitUntil: 'networkidle0'
        });

        // PDFを生成
        await page.pdf({
            path: outputPDF,
            format: 'A4',
            margin: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
            printBackground: true,
            displayHeaderFooter: false,
            preferCSSPageSize: true
        });

        await browser.close();

        console.log(`✓ PDF生成完了: ${outputPDF}`);
    } catch (error) {
        console.error('エラーが発生しました:', error);
        process.exit(1);
    }
}

generatePDF();
